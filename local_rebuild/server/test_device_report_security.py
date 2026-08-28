"""Integration tests: device enrollment + signed/encrypted reports end-to-end."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
import uuid

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from local_rebuild.server.app import create_app
from local_rebuild.server.device_crypto import encrypt_hybrid


class DeviceClient:
    """Minimal in-test stand-in for the APK crypto side."""

    def __init__(self) -> None:
        self.rsa = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.public_pem = self.rsa.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode()
        self.device_id = ""
        self.secret = b""

    def enroll(self, client, user_id: str = "199504987") -> None:
        resp = client.post("/api/device/enroll", json={
            "userId": user_id, "accountId": "198716", "devicePublicKey": self.public_pem,
        })
        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]
        self.device_id = data["device_id"]
        self.secret = self.rsa.decrypt(
            base64.b64decode(data["enc_hmac_secret"]),
            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
        )
        assert len(self.secret) == 32

    def signed_headers(self, method: str, path: str, body: bytes) -> dict[str, str]:
        ts = str(int(time.time()))
        nonce = uuid.uuid4().hex
        canonical = f"{method}\n{path}\n{ts}\n{nonce}\n".encode() + hashlib.sha256(body).hexdigest().encode()
        return {
            "X-Device-Id": self.device_id,
            "X-Timestamp": ts,
            "X-Nonce": nonce,
            "X-Sign": hmac.new(self.secret, canonical, hashlib.sha256).hexdigest(),
        }

    def encrypted_body(self, server_public_pem: str, payload: dict) -> dict:
        return encrypt_hybrid(server_public_pem.encode(), json.dumps(payload).encode())


def _make_client(monkeypatch, enforce: bool):
    import tempfile
    from pathlib import Path
    from fastapi.testclient import TestClient
    if enforce:
        monkeypatch.setenv("DEVICE_SIGN_ENFORCE", "1")
    else:
        monkeypatch.delenv("DEVICE_SIGN_ENFORCE", raising=False)
    app = create_app(Path(tempfile.mkdtemp()) / "events.jsonl")
    return TestClient(app)


class TestEnrollEndpoint:
    def test_enroll_returns_encrypted_secret(self, monkeypatch):
        client = _make_client(monkeypatch, enforce=False)
        dev = DeviceClient()
        dev.enroll(client)
        assert dev.device_id
        assert dev.secret

    def test_enroll_rejects_bad_key(self, monkeypatch):
        client = _make_client(monkeypatch, enforce=False)
        resp = client.post("/api/device/enroll", json={"userId": "u", "devicePublicKey": "junk"})
        assert resp.status_code == 400
        assert resp.json()["code"] != 0


class TestSignedEncryptedReports:
    def test_signed_encrypted_mark_paid_accepted_and_decrypted(self, monkeypatch):
        client = _make_client(monkeypatch, enforce=False)
        dev = DeviceClient()
        dev.enroll(client)
        server_pub = client.post("/api/device/enroll", json={
            "userId": "199504987", "accountId": "198716", "devicePublicKey": dev.public_pem,
        }).json()["data"]["server_public_key"]
        wrapped = dev.encrypted_body(server_pub, {"pay_id": "BILL_42"})
        body = json.dumps(wrapped).encode()
        resp = client.post("/api/device/mark_paid", content=body,
                           headers={"Content-Type": "application/json", **dev.signed_headers("POST", "/api/device/mark_paid", body)})
        assert resp.status_code == 200, resp.text
        assert resp.json()["code"] == 0

    def test_tampered_signature_log_only_still_accepts(self, monkeypatch):
        client = _make_client(monkeypatch, enforce=False)
        dev = DeviceClient()
        dev.enroll(client)
        body = b'{"pay_id":"B_1"}'
        headers = dev.signed_headers("POST", "/api/device/mark_paid", body)
        headers["X-Sign"] = "0" * 64
        resp = client.post("/api/device/mark_paid", content=body,
                           headers={"Content-Type": "application/json", **headers})
        assert resp.status_code == 200  # log-only mode
        # security event recorded
        events = [json.loads(l) for l in client.app.state.event_log_path.read_text().splitlines()]
        assert any(e.get("type") == "security.device_sign_rejected" or
                   (isinstance(e.get("payload"), dict) and e["payload"].get("security") == "device.sign_rejected")
                   for e in events)

    def test_enforce_mode_rejects_unsigned(self, monkeypatch):
        client = _make_client(monkeypatch, enforce=True)
        resp = client.post("/api/device/mark_paid", json={"pay_id": "B_1"})
        assert resp.status_code == 401
        assert resp.json()["code"] != 0

    def test_enforce_mode_rejects_bad_signature(self, monkeypatch):
        client = _make_client(monkeypatch, enforce=True)
        dev = DeviceClient()
        dev.enroll(client)
        body = b'{"pay_id":"B_1"}'
        headers = dev.signed_headers("POST", "/api/device/mark_paid", body)
        headers["X-Sign"] = "f" * 64
        resp = client.post("/api/device/mark_paid", content=body,
                           headers={"Content-Type": "application/json", **headers})
        assert resp.status_code == 401

    def test_enforce_mode_accepts_valid_signed(self, monkeypatch):
        client = _make_client(monkeypatch, enforce=True)
        dev = DeviceClient()
        dev.enroll(client)
        body = b'{"pay_id":"B_1"}'
        resp = client.post("/api/device/mark_paid", content=body,
                           headers={"Content-Type": "application/json", **dev.signed_headers("POST", "/api/device/mark_paid", body)})
        assert resp.status_code == 200
        assert resp.json()["code"] == 0

    def test_legacy_unsigned_still_works_in_log_only(self, monkeypatch):
        client = _make_client(monkeypatch, enforce=False)
        resp = client.post("/api/device/mark_paid", json={"pay_id": "B_1"})
        assert resp.status_code == 200
        assert resp.json()["code"] == 0
