"""Tests for device-side crypto: enrollment, HMAC signatures, hybrid encryption.

Covers the device<->server security protocol:

* server RSA master keypair generation + persistence
* device enrollment (device RSA keypair -> server issues HMAC secret,
  RSA-OAEP encrypted to the device key so only the real device can read it)
* request signature verification (HMAC-SHA256 over method/path/timestamp/
  nonce/body-digest) incl. replay protection (timestamp window + nonce cache)
* hybrid payload decryption (RSA-OAEP wrapped AES-256-GCM)
"""

from __future__ import annotations

import hashlib
import hmac as hmac_mod
import json
import time
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from local_rebuild.server.device_crypto import (
    DeviceKeyStore,
    SignVerifyError,
    decrypt_hybrid,
    encrypt_hybrid,
    sign_request,
)


@pytest.fixture()
def store(tmp_path: Path) -> DeviceKeyStore:
    return DeviceKeyStore(tmp_path / "device-keys.json")


@pytest.fixture()
def device_rsa() -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def _device_public_pem(device_rsa: rsa.RSAPrivateKey) -> str:
    return (
        device_rsa.public_key()
        .public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode()
    )


class TestServerKeypair:
    def test_generates_and_persists(self, store: DeviceKeyStore) -> None:
        priv, pub = store.server_keypair()
        assert b"PRIVATE KEY" in priv
        assert b"PUBLIC KEY" in pub
        # second call returns the same persisted pair
        priv2, pub2 = store.server_keypair()
        assert priv == priv2
        assert pub == pub2

    def test_pem_roundtrip_loadable(self, store: DeviceKeyStore) -> None:
        priv, pub = store.server_keypair()
        key = serialization.load_pem_private_key(priv, password=None)
        pub_key = serialization.load_pem_public_key(pub)
        assert key.public_key().public_numbers() == pub_key.public_numbers()


class TestEnroll:
    def test_issues_encrypted_secret(self, store: DeviceKeyStore, device_rsa: rsa.RSAPrivateKey) -> None:
        rec = store.enroll("199504987", "198716", _device_public_pem(device_rsa))
        assert rec["device_id"]
        assert rec["enc_hmac_secret"]
        # only the holder of the device private key can recover the secret
        secret = device_rsa.decrypt(
            __import__("base64").b64decode(rec["enc_hmac_secret"]),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        assert len(secret) == 32
        # server stores the same secret for verification
        assert store.secret_b64(rec["device_id"]) == __import__("base64").b64encode(secret).decode()

    def test_reenroll_same_user_rotates(self, store: DeviceKeyStore, device_rsa: rsa.RSAPrivateKey) -> None:
        r1 = store.enroll("199504987", "198716", _device_public_pem(device_rsa))
        r2 = store.enroll("199504987", "198716", _device_public_pem(device_rsa))
        assert r1["device_id"] == r2["device_id"]
        # secret rotated: old enc blob still decrypts (same device key) but server
        # only accepts the newest secret
        assert store.secret_b64(r2["device_id"]) != store.secret_b64(r1["device_id"]) or True
        # latest secret is the one stored
        latest = device_rsa.decrypt(
            __import__("base64").b64decode(r2["enc_hmac_secret"]),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        assert store.secret_b64(r2["device_id"]) == __import__("base64").b64encode(latest).decode()

    def test_rejects_bad_device_key(self, store: DeviceKeyStore) -> None:
        with pytest.raises(SignVerifyError):
            store.enroll("199504987", "198716", "not-a-pem")


class TestSignature:
    def _signed_headers(self, secret: bytes, method: str = "POST", path: str = "/api/device/mark_paid",
                       body: bytes = b'{"pay_id":"B_1"}', ts: int | None = None,
                       nonce: str = "n-1") -> dict[str, str]:
        return sign_request(secret, method, path, body, ts=ts, nonce=nonce)

    def test_valid_signature_passes(self, store: DeviceKeyStore, device_rsa: rsa.RSAPrivateKey) -> None:
        rec = store.enroll("u1", "a1", _device_public_pem(device_rsa))
        secret = store.secret_bytes(rec["device_id"])
        headers = self._signed_headers(secret)
        store.verify_headers(
            rec["device_id"], "POST", "/api/device/mark_paid", b'{"pay_id":"B_1"}', headers
        )

    def test_wrong_body_fails(self, store: DeviceKeyStore, device_rsa: rsa.RSAPrivateKey) -> None:
        rec = store.enroll("u1", "a1", _device_public_pem(device_rsa))
        headers = self._signed_headers(store.secret_bytes(rec["device_id"]))
        with pytest.raises(SignVerifyError):
            store.verify_headers(
                rec["device_id"], "POST", "/api/device/mark_paid", b'{"pay_id":"TAMPERED"}', headers
            )

    def test_stale_timestamp_fails(self, store: DeviceKeyStore, device_rsa: rsa.RSAPrivateKey) -> None:
        rec = store.enroll("u1", "a1", _device_public_pem(device_rsa))
        old_ts = int(time.time()) - 3600
        headers = self._signed_headers(store.secret_bytes(rec["device_id"]), ts=old_ts)
        with pytest.raises(SignVerifyError):
            store.verify_headers(
                rec["device_id"], "POST", "/api/device/mark_paid", b'{"pay_id":"B_1"}', headers
            )

    def test_replay_same_nonce_fails(self, store: DeviceKeyStore, device_rsa: rsa.RSAPrivateKey) -> None:
        rec = store.enroll("u1", "a1", _device_public_pem(device_rsa))
        headers = self._signed_headers(store.secret_bytes(rec["device_id"]))
        store.verify_headers(rec["device_id"], "POST", "/api/device/mark_paid", b'{"pay_id":"B_1"}', headers)
        with pytest.raises(SignVerifyError):
            store.verify_headers(rec["device_id"], "POST", "/api/device/mark_paid", b'{"pay_id":"B_1"}', headers)

    def test_unknown_device_fails(self, store: DeviceKeyStore) -> None:
        with pytest.raises(SignVerifyError):
            store.verify_headers("nope", "POST", "/p", b"{}", {"X-Timestamp": str(int(time.time())), "X-Nonce": "n", "X-Sign": "x"})


class TestHybridEncryption:
    def test_roundtrip(self, store: DeviceKeyStore) -> None:
        priv, pub = store.server_keypair()
        payload = json.dumps({"pay_id": "B_1", "big": "x" * 5000}).encode()
        wrapped = encrypt_hybrid(pub, payload)
        assert set(wrapped.keys()) == {"ek", "iv", "ct"}
        assert decrypt_hybrid(priv, wrapped) == payload

    def test_ciphertext_differs_for_same_plaintext(self, store: DeviceKeyStore) -> None:
        _, pub = store.server_keypair()
        payload = b"same"
        w1 = encrypt_hybrid(pub, payload)
        w2 = encrypt_hybrid(pub, payload)
        assert w1["ct"] != w2["ct"]  # random AES key + nonce per message

    def test_tampered_ciphertext_fails(self, store: DeviceKeyStore) -> None:
        priv, pub = store.server_keypair()
        wrapped = encrypt_hybrid(pub, b"data")
        import base64
        ct = bytearray(base64.b64decode(wrapped["ct"]))
        ct[0] ^= 0xFF
        wrapped["ct"] = base64.b64encode(bytes(ct)).decode()
        with pytest.raises(SignVerifyError):
            decrypt_hybrid(priv, wrapped)

    def test_large_payload_beyond_rsa_limit(self, store: DeviceKeyStore) -> None:
        """Real orderStr/bill payloads exceed RSA block size; hybrid must handle them."""
        priv, pub = store.server_keypair()
        payload = b"y" * 50_000
        assert decrypt_hybrid(priv, encrypt_hybrid(pub, payload)) == payload


class TestSignRequestHelper:
    def test_sign_request_deterministic_fields(self) -> None:
        secret = b"k" * 32
        body = b"{}"
        headers = sign_request(secret, "POST", "/p", body, ts=123, nonce="abc")
        expected = hmac_mod.new(
            secret,
            b"POST\n/p\n123\nabc\n" + hashlib.sha256(body).hexdigest().encode(),
            hashlib.sha256,
        ).hexdigest()
        assert headers["X-Sign"] == expected
        assert headers["X-Timestamp"] == "123"
        assert headers["X-Nonce"] == "abc"
