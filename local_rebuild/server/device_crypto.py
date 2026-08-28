"""Device-side crypto for the APK<->server protocol.

Threat model: the mock server is reachable on the public internet; device
reports (payment notifications in particular) must not be forgeable by
third parties.  This module implements:

* a persisted server RSA master keypair
* device enrollment: the device posts its own RSA public key, the server
  issues a per-device HMAC-SHA256 secret **encrypted to the device key**
  (RSA-OAEP) so only the genuine device can recover it
* request signature verification: ``X-Sign`` = HMAC-SHA256 over
  ``method\\npath\\ntimestamp\\nnonce\\nsha256hex(body)`` with a timestamp
  window and a nonce replay cache
* hybrid payload encryption: random AES-256-GCM key encrypts the body,
  RSA-OAEP(server public) wraps the AES key -- RSA alone cannot carry
  multi-KB payloads such as real orderStr/bill models

Known limitation (documented, accepted for this test system): enrollment
runs over plain HTTP, so an on-path MITM can substitute the device public
key during enrollment.  The scheme defeats off-path forgery and replay,
not active MITM; that would require TLS.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
import uuid
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature, InvalidTag
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

TIMESTAMP_WINDOW_SECONDS = 300
NONCE_CACHE_SIZE = 4096


class SignVerifyError(Exception):
    """Raised when enrollment, signature verification or decryption fails."""


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode()


def _unb64(data: str) -> bytes:
    return base64.b64decode(data)


def sign_request(
    secret: bytes,
    method: str,
    path: str,
    body: bytes,
    ts: int | None = None,
    nonce: str | None = None,
) -> dict[str, str]:
    """Build the signature headers for a device report.

    The canonical string is ``method\\npath\\ntimestamp\\nnonce\\nsha256hex(body)``,
    HMAC'd with SHA-256 using the per-device secret.
    """
    ts = ts if ts is not None else int(time.time())
    nonce = nonce if nonce is not None else uuid.uuid4().hex
    canonical = (
        f"{method.upper()}\n{path}\n{ts}\n{nonce}\n".encode()
        + hashlib.sha256(body).hexdigest().encode()
    )
    sign = hmac.new(secret, canonical, hashlib.sha256).hexdigest()
    return {
        "X-Device-Id": "",  # filled by caller (needs enrollment context)
        "X-Timestamp": str(ts),
        "X-Nonce": nonce,
        "X-Sign": sign,
    }


def encrypt_hybrid(server_public_pem: bytes, payload: bytes) -> dict[str, str]:
    """Encrypt *payload* with a fresh AES-256-GCM key; wrap that key with RSA-OAEP."""
    public_key = serialization.load_pem_public_key(server_public_pem)
    aes_key = AESGCM.generate_key(bit_length=256)
    iv = secrets.token_bytes(12)
    ct = AESGCM(aes_key).encrypt(iv, payload, None)
    ek = public_key.encrypt(
        aes_key,
        asym_padding.OAEP(
            mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    return {"ek": _b64(ek), "iv": _b64(iv), "ct": _b64(ct)}


def decrypt_hybrid(server_private_pem: bytes, wrapped: dict[str, str]) -> bytes:
    """Invert :func:`encrypt_hybrid`; raises SignVerifyError on any failure."""
    try:
        private_key = serialization.load_pem_private_key(server_private_pem, password=None)
        aes_key = private_key.decrypt(
            _unb64(wrapped["ek"]),
            asym_padding.OAEP(
                mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        return AESGCM(aes_key).decrypt(_unb64(wrapped["iv"]), _unb64(wrapped["ct"]), None)
    except (KeyError, InvalidTag, ValueError) as exc:
        raise SignVerifyError(f"hybrid decrypt failed: {exc}") from exc


class DeviceKeyStore:
    """Persists the server keypair and per-device enrollment records as JSON."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._nonces: dict[str, float] = {}  # nonce -> first-seen timestamp
        self._devices: dict[str, dict[str, Any]] = {}
        self._load()

    # ------------------------------------------------------------- storage
    def _load(self) -> None:
        if not self.path.exists():
            self._data: dict[str, Any] = {"server_key": None, "devices": {}}
        else:
            try:
                self._data = json.loads(self.path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                self._data = {"server_key": None, "devices": {}}
        self._devices = self._data.setdefault("devices", {})

    def _save(self) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._data, ensure_ascii=False, indent=1), encoding="utf-8")
        os.replace(tmp, self.path)

    # -------------------------------------------------------- server keypair
    def server_keypair(self) -> tuple[bytes, bytes]:
        """Return (private_pem, public_pem), generating + persisting on first use."""
        cached = self._data.get("server_key")
        if cached:
            return cached["private_pem"].encode(), cached["public_pem"].encode()
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        priv_pem = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode()
        pub_pem = key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode()
        self._data["server_key"] = {"private_pem": priv_pem, "public_pem": pub_pem}
        self._save()
        return priv_pem.encode(), pub_pem.encode()

    # -------------------------------------------------------------- enroll
    def enroll(self, user_id: str, account_id: str, device_public_pem: str) -> dict[str, str]:
        """Register a device: issue device_id + HMAC secret encrypted to its key."""
        try:
            device_pub = serialization.load_pem_public_key(device_public_pem.encode())
            if not isinstance(device_pub, rsa.RSAPublicKey):
                raise ValueError("not an RSA public key")
        except (ValueError, TypeError) as exc:
            raise SignVerifyError(f"invalid device public key: {exc}") from exc

        existing = next(
            (d for d in self._devices.values() if d.get("user_id") == user_id), None
        )
        device_id = existing["device_id"] if existing else uuid.uuid4().hex
        hmac_secret = secrets.token_bytes(32)
        enc_secret = device_pub.encrypt(
            hmac_secret,
            asym_padding.OAEP(
                mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        _, server_pub = self.server_keypair()
        self._devices[device_id] = {
            "device_id": device_id,
            "user_id": user_id,
            "account_id": account_id,
            "device_public_pem": device_public_pem,
            "hmac_secret_b64": _b64(hmac_secret),
            "enrolled_at": int(time.time()),
        }
        self._save()
        return {
            "device_id": device_id,
            "server_public_key": server_pub.decode(),
            "enc_hmac_secret": _b64(enc_secret),
        }

    # ---------------------------------------------------------- verification
    def _secret_bytes(self, device_id: str) -> bytes:
        rec = self._devices.get(device_id)
        if not rec:
            raise SignVerifyError(f"unknown device: {device_id}")
        return _unb64(rec["hmac_secret_b64"])

    def secret_b64(self, device_id: str) -> str:
        return self._devices[device_id]["hmac_secret_b64"]

    def secret_bytes(self, device_id: str) -> bytes:
        return self._secret_bytes(device_id)

    def device_id_for_user(self, user_id: str) -> str | None:
        """Return the enrolled device_id for *user_id*, or None."""
        rec = next((d for d in self._devices.values() if d.get("user_id") == user_id), None)
        return rec["device_id"] if rec else None

    def _check_nonce(self, nonce: str, now: float) -> None:
        # evict expired entries lazily
        cutoff = now - TIMESTAMP_WINDOW_SECONDS * 2
        if len(self._nonces) > NONCE_CACHE_SIZE:
            self._nonces = {n: t for n, t in self._nonces.items() if t > cutoff}
        if nonce in self._nonces:
            raise SignVerifyError("replayed nonce")
        self._nonces[nonce] = now

    def verify_headers(
        self,
        device_id: str,
        method: str,
        path: str,
        body: bytes,
        headers: dict[str, str],
    ) -> None:
        """Verify X-Timestamp/X-Nonce/X-Sign for a device report; raises on failure."""
        # ASGI 头名一律小写；这里做大小写不敏感查找以兼容不同客户端
        lower = {str(k).lower(): v for k, v in headers.items()}
        try:
            ts = int(lower["x-timestamp"])
            nonce = lower["x-nonce"]
            sign = lower["x-sign"]
        except (KeyError, ValueError) as exc:
            raise SignVerifyError(f"missing signature headers: {exc}") from exc
        now = time.time()
        if abs(now - ts) > TIMESTAMP_WINDOW_SECONDS:
            raise SignVerifyError(f"timestamp outside ±{TIMESTAMP_WINDOW_SECONDS}s window")
        self._check_nonce(nonce, now)
        secret = self._secret_bytes(device_id)
        canonical = (
            f"{method.upper()}\n{path}\n{ts}\n{nonce}\n".encode()
            + hashlib.sha256(body).hexdigest().encode()
        )
        expected = hmac.new(secret, canonical, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, sign):
            raise SignVerifyError("signature mismatch")

    def verify_ws_envelope(self, device_id: str, envelope: dict[str, Any]) -> bool:
        """Verify a signed WS envelope (``data.sig`` over ``data.ts/nonce/payload``).

        Returns True when the envelope carries a valid signature; False when it
        carries none (legacy device); raises SignVerifyError on an invalid one.
        """
        data = envelope.get("data")
        if not isinstance(data, dict):
            return False
        sig = data.get("sig")
        if not sig:
            return False
        try:
            ts = int(data["ts"])
            nonce = str(data["nonce"])
        except (KeyError, ValueError) as exc:
            raise SignVerifyError(f"bad ws signature fields: {exc}") from exc
        now = time.time()
        if abs(now - ts) > TIMESTAMP_WINDOW_SECONDS:
            raise SignVerifyError("ws timestamp outside window")
        self._check_nonce(device_id + ":" + nonce, now)
        secret = self._secret_bytes(device_id)
        payload = json.dumps(
            {k: v for k, v in data.items() if k != "sig"},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        expected = hmac.new(secret, payload, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, str(sig)):
            raise SignVerifyError("ws signature mismatch")
        return True
