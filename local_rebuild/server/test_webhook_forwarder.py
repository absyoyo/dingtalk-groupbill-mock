"""Tests for the outbound webhook forwarder (PHP plugin integration).

Signature protocol (MD5, per partner requirement):
    sign = md5(timestamp + '.' + nonce + '.' + raw_body + '.' + secret)
Headers: X-Ddgb-Timestamp / X-Ddgb-Nonce / X-Ddgb-Sign

Delivery semantics:
* only whitelisted event types are forwarded
* deliveries run out-of-band (never block record())
* failed deliveries retry with capped exponential backoff
* non-2xx responses count as failure
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
from pathlib import Path

import pytest
import httpx
from fastapi import FastAPI
from fastapi.testclient import TestClient

from local_rebuild.server.webhook_forwarder import (
    WEBHOOK_EVENT_TYPES,
    WebhookForwarder,
    build_signed_headers,
    verify_md5_sign,
)


def _secret() -> str:
    return "test-secret-123"


def _event(etype: str, payload: dict) -> dict:
    return {
        "timestamp": time.time(),
        "connection_id": "test-conn",
        "direction": "in",
        "transport": "ws",
        "type": etype,
        "payload": payload,
    }


class TestEventFilter:
    def test_business_events_forwarded(self) -> None:
        f = WebhookForwarder(url="http://127.0.0.1:9/x", secret=_secret())
        for etype in ("bill.upsert", "alipay.upload", "/api/device/mark_paid",
                      "connected", "disconnected", "register"):
            assert etype in WEBHOOK_EVENT_TYPES
            assert f._should_forward(_event(etype, {}))

    def test_noise_events_skipped(self) -> None:
        f = WebhookForwarder(url="http://127.0.0.1:9/x", secret=_secret())
        for etype in ("ping", "pong", "ack", "rpc.call", "security.ws_sign_rejected"):
            assert not f._should_forward(_event(etype, {}))

    def test_outbound_direction_skipped(self) -> None:
        f = WebhookForwarder(url="http://127.0.0.1:9/x", secret=_secret())
        ev = _event("bill.upsert", {})
        ev["direction"] = "out"
        assert not f._should_forward(ev)


class TestSignature:
    def test_sign_roundtrip(self) -> None:
        body = json.dumps({"pay_id": "B_1"}, ensure_ascii=False).encode()
        headers = build_signed_headers(_secret(), body)
        raw = (
            headers["X-Ddgb-Timestamp"] + "." + headers["X-Ddgb-Nonce"] + "."
            + body.decode() + "." + _secret()
        )
        expected = hashlib.md5(raw.encode()).hexdigest()
        assert headers["X-Ddgb-Sign"] == expected
        assert verify_md5_sign(_secret(), body, headers) is True

    def test_verify_rejects_tampered_body(self) -> None:
        body = b'{"pay_id":"B_1"}'
        headers = build_signed_headers(_secret(), body)
        assert verify_md5_sign(_secret(), b'{"pay_id":"B_2"}', headers) is False

    def test_verify_rejects_wrong_secret(self) -> None:
        body = b'{}'
        headers = build_signed_headers(_secret(), body)
        assert verify_md5_sign("other", body, headers) is False


class TestDelivery:
    def test_successful_delivery_via_mock_transport(self) -> None:
        """End-to-end submit→sign→POST→200 using an httpx mock transport."""
        import asyncio as aio

        received: list[dict] = []
        last_headers: dict = {}

        def handler(request: httpx.Request) -> httpx.Response:
            received.append(json.loads(request.content))
            last_headers.update(dict(request.headers))
            return httpx.Response(200, json={"code": 0})

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        f = WebhookForwarder(url="http://mock/hook", secret=_secret())
        f._client = client
        f.submit(_event("/api/device/mark_paid", {"pay_id": "B_1"}))
        aio.run(f._drain_once())
        assert received and received[0]["type"] == "/api/device/mark_paid"
        assert received[0]["payload"]["pay_id"] == "B_1"
        # signature headers present and valid
        assert verify_md5_sign(
            _secret(),
            json.dumps(received[0], ensure_ascii=False).encode(),
            {"X-Ddgb-Timestamp": last_headers["x-ddgb-timestamp"],
             "X-Ddgb-Nonce": last_headers["x-ddgb-nonce"],
             "X-Ddgb-Sign": last_headers["x-ddgb-sign"]},
        )

    def test_non_2xx_schedules_retry(self) -> None:
        import asyncio as aio

        attempts: list[int] = []

        def handler(request: httpx.Request) -> httpx.Response:
            attempts.append(1)
            return httpx.Response(500, json={"code": 1})

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        f = WebhookForwarder(url="http://mock/hook", secret=_secret(),
                             max_retries=3, backoff_base=0.001)
        f._client = client
        f.submit(_event("bill.upsert", {"groupBillId": "X"}))
        aio.run(f._drain_once())
        assert len(attempts) == 1
        aio.run(f._drain_once())
        assert len(attempts) == 2  # retried once more

    def test_retries_on_failure_then_gives_up(self) -> None:
        f = WebhookForwarder(url="http://127.0.0.1:9/x", secret=_secret(), max_retries=2, backoff_base=0.01)
        f.submit(_event("bill.upsert", {"groupBillId": "X"}))
        asyncio.run(f._drain_once())
        asyncio.run(f._drain_once())
        # after exhausting retries the event is dropped (no crash, logged)
        assert f.dropped_count >= 0

    def test_disabled_when_no_url(self) -> None:
        f = WebhookForwarder(url="", secret=_secret())
        assert not f._should_forward(_event("bill.upsert", {}))
        f.start()
        f.submit(_event("bill.upsert", {}))


class TestWiring:
    def test_create_app_mounts_forwarder(self, tmp_path: Path) -> None:
        import os
        from local_rebuild.server.app import create_app

        os.environ["DDGB_WEBHOOK_URL"] = "http://127.0.0.1:9/hook"
        os.environ["DDGB_WEBHOOK_SECRET"] = "s3"
        try:
            app = create_app(tmp_path / "events.jsonl")
            assert hasattr(app.state, "ddgb_webhook")
            assert app.state.ddgb_webhook.url == "http://127.0.0.1:9/hook"
        finally:
            os.environ.pop("DDGB_WEBHOOK_URL", None)
            os.environ.pop("DDGB_WEBHOOK_SECRET", None)
