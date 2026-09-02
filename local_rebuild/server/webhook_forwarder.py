"""Outbound webhook forwarder for PHP-plugin integration (dingtalk_groupbill).

Subscribes to the in-process EventHub and POSTs business events (bill
creation, pay-url ready, payment receipts, device presence) to a partner
endpoint configured via environment variables:

* ``DDGB_WEBHOOK_URL``    — partner endpoint; empty/unset disables forwarding
* ``DDGB_WEBHOOK_SECRET`` — shared secret for the simple MD5 signature

Signature protocol (partner chose MD5 for simplicity):

    sign = md5("{timestamp}.{nonce}.{body}.{secret}")

sent as ``X-Ddgb-Timestamp`` / ``X-Ddgb-Nonce`` / ``X-Ddgb-Sign`` headers.
The PHP side recomputes the digest over timestamp + '.' + nonce + '.' +
raw_body + '.' + secret.  Non-2xx responses and network errors retry with
capped exponential backoff up to ``max_retries``, after which the event is
dropped (the PHP side's reconciliation job re-syncs from the bills API).

The forwarder never raises into the caller: ``submit()`` is fire-and-forget
so event recording on the Python side is never blocked by partner downtime.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import time
import uuid
from typing import Any

import httpx

logger = logging.getLogger("ddgb.webhook")

# Only business-relevant events cross the boundary; transport noise
# (ping/pong/ack), server-originated commands (rpc.call) and internal
# security logs stay on this side.
WEBHOOK_EVENT_TYPES: frozenset[str] = frozenset({
    "bill.upsert",            # new/updated group bill → PHP order pool
    "alipay.upload",          # pay-url ready (orderStr)
    "/api/device/mark_paid",  # payer paid (pay_id = billId_payerUid)
    "connected",              # device WS connected
    "disconnected",           # device WS dropped
    "register",               # device registered its uid
})

_LOOP_INTERVAL = 0.2
_MAX_QUEUE = 1000


def build_signed_headers(secret: str, body: bytes) -> dict[str, str]:
    """Build MD5-signed headers for one webhook delivery."""
    ts = str(int(time.time()))
    nonce = uuid.uuid4().hex
    raw = f"{ts}.{nonce}.{body.decode('utf-8')}.{secret}"
    sign = hashlib.md5(raw.encode("utf-8")).hexdigest()
    return {
        "X-Ddgb-Timestamp": ts,
        "X-Ddgb-Nonce": nonce,
        "X-Ddgb-Sign": sign,
    }


def verify_md5_sign(secret: str, body: bytes, headers: dict[str, str]) -> bool:
    """Verify a delivery (used by tests; PHP mirrors this check)."""
    lower = {str(k).lower(): str(v) for k, v in headers.items()}
    ts = lower.get("x-ddgb-timestamp", "")
    nonce = lower.get("x-ddgb-nonce", "")
    sign = lower.get("x-ddgb-sign", "")
    if not ts or not nonce or not sign:
        return False
    raw = f"{ts}.{nonce}.{body.decode('utf-8')}.{secret}"
    expected = hashlib.md5(raw.encode("utf-8")).hexdigest()
    return expected == sign


class WebhookForwarder:
    """Fan business events out to one partner endpoint, best-effort."""

    def __init__(
        self,
        url: str,
        secret: str,
        *,
        max_retries: int = 5,
        backoff_base: float = 1.0,
        backoff_cap: float = 60.0,
        timeout: float = 8.0,
    ) -> None:
        self.url = (url or "").strip()
        self.secret = secret or ""
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.backoff_cap = backoff_cap
        self.timeout = timeout
        self.enabled = bool(self.url and self.secret)
        self.dropped_count = 0
        self._queue: asyncio.Queue[tuple[dict[str, Any], int]] = asyncio.Queue(maxsize=_MAX_QUEUE)
        self._task: asyncio.Task | None = None
        self._client: httpx.AsyncClient | None = None

    # ------------------------------------------------------------ lifecycle
    def start(self) -> None:
        if not self.enabled or self._task is not None:
            return
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return  # no running loop (e.g. unit tests); delivery stays queued
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        self._task = loop.create_task(self._run())

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except (asyncio.CancelledError, Exception):
                pass
            self._task = None
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    # ------------------------------------------------------------ ingestion
    def _should_forward(self, event: dict[str, Any]) -> bool:
        if not self.enabled:
            return False
        if event.get("direction") != "in":
            return False
        return event.get("type") in WEBHOOK_EVENT_TYPES

    def submit(self, event: dict[str, Any]) -> None:
        """Enqueue one event for delivery; never raises."""
        if not self._should_forward(event):
            return
        try:
            self._queue.put_nowait((event, 0))
        except asyncio.QueueFull:
            self.dropped_count += 1
            logger.warning("webhook queue full, dropped event type=%s", event.get("type"))

    # ------------------------------------------------------------ delivery
    async def _run(self) -> None:
        while True:
            await self._drain_once()
            await asyncio.sleep(_LOOP_INTERVAL)

    async def _drain_once(self) -> None:
        """Deliver one queued event (or retry one failed delivery)."""
        try:
            event, attempt = self._queue.get_nowait()
        except asyncio.QueueEmpty:
            return
        if attempt >= self.max_retries:
            self.dropped_count += 1
            logger.error(
                "webhook give up after %d attempts type=%s", attempt, event.get("type")
            )
            return
        body = json.dumps(event, ensure_ascii=False).encode("utf-8")
        headers = build_signed_headers(self.secret, body)
        ok = False
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        try:
            resp = await self._client.post(self.url, content=body, headers={
                "Content-Type": "application/json",
                **headers,
            })
            ok = 200 <= resp.status_code < 300
        except Exception as exc:  # network error
            logger.warning("webhook delivery error: %s", exc)
        if ok:
            return
        backoff = min(self.backoff_base * (2 ** attempt), self.backoff_cap)
        await asyncio.sleep(backoff)
        try:
            self._queue.put_nowait((event, attempt + 1))
        except asyncio.QueueFull:
            self.dropped_count += 1
