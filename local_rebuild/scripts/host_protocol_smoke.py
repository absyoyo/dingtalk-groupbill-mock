"""Host-side protocol smoke test for the local mock service.

Verifies HTTP health, WebSocket register/ack, server-to-client debug
delivery of bill.task, and HTTP upload_order recording against a
live ``127.0.0.1:18722`` service.  Prints ``host-protocol-smoke-ok``
on success and raises :class:`AssertionError` on any check failure.

Usage::

    python3 local_rebuild/scripts/host_protocol_smoke.py
"""

import asyncio
import json

import httpx
import websockets


async def main() -> None:
    """Run all smoke checks against the local mock server."""
    async with httpx.AsyncClient(
        base_url="http://127.0.0.1:18722",
        timeout=httpx.Timeout(10.0),
    ) as client:
        health = await client.get("/health")
        assert health.json()["code"] == 0, "health check failed"

        async with websockets.connect(
            "ws://127.0.0.1:18722/ws",
            open_timeout=10,
            close_timeout=5,
        ) as ws:
            await asyncio.wait_for(
                ws.send(json.dumps({"type": "register", "data": {"userId": "host-smoke"}})),
                timeout=10,
            )
            ack = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))
            assert ack == {
                "type": "ack",
                "data": {"message": "registered", "userId": "host-smoke", "pendingTasks": 0},
            }, f"unexpected ack: {ack}"

            response = await client.post("/debug/ws/send", json={"type": "bill.task", "data": {"taskId": "smoke-task"}})
            assert response.json()["code"] == 0, "debug ws send failed"
            delivered = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))
            assert delivered == {"type": "bill.task", "data": {"taskId": "smoke-task"}}, f"unexpected delivery: {delivered}"

        upload = await client.post(
            "/api/device/upload_order",
            json={"user": "host-smoke", "pay_order": "order-smoke", "pay_id": "pay-smoke", "amount": 1.0},
        )
        assert upload.json()["code"] == 0, "upload_order failed"

    print("host-protocol-smoke-ok")


if __name__ == "__main__":
    asyncio.run(main())
