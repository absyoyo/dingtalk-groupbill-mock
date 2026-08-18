import json
from unittest.mock import AsyncMock

import pytest
from starlette.websockets import WebSocketDisconnect


def test_ws_register_ack_and_ping_pong(client, events):
    with client.websocket_connect("/ws") as ws:
        ws.send_text(json.dumps({"type": "register", "data": {"userId": "alice"}}))
        ack = json.loads(ws.receive_text())
        assert ack == {
            "type": "ack",
            "data": {"message": "registered", "userId": "alice", "pendingTasks": 0},
        }

        ws.send_text(json.dumps({"type": "ping", "data": "hello-world"}))
        pong = json.loads(ws.receive_text())
        assert pong == {"type": "pong", "data": "hello-world"}

    all_events = events()
    ws_in = [e for e in all_events if e["transport"] == "ws" and e["direction"] == "in"]
    ws_out = [e for e in all_events if e["transport"] == "ws" and e["direction"] == "out"]
    assert len(ws_in) >= 2
    assert len(ws_out) >= 2
    assert "register" in [e["type"] for e in ws_in]
    assert "ping" in [e["type"] for e in ws_in]
    assert "ack" in [e["type"] for e in ws_out]
    assert "pong" in [e["type"] for e in ws_out]


def test_ws_bill_upsert_logged(client, events):
    with client.websocket_connect("/ws") as ws:
        ws.send_text(json.dumps({"type": "register", "data": {"userId": "bob"}}))
        ack = json.loads(ws.receive_text())
        assert ack == {
            "type": "ack",
            "data": {"message": "registered", "userId": "bob", "pendingTasks": 0},
        }

        ws.send_text(json.dumps({"type": "bill.upsert", "data": {"bill_id": "B001", "amount": 99.99}}))

    bill_events = [
        e
        for e in events()
        if e["transport"] == "ws" and e["direction"] == "in" and e["type"] == "bill.upsert"
    ]
    assert len(bill_events) == 1
    assert bill_events[0]["payload"] == {"type": "bill.upsert", "data": {"bill_id": "B001", "amount": 99.99}}


def test_ws_malformed_json_returns_parse_error(client, events):
    with client.websocket_connect("/ws") as ws:
        ws.send_text("not-json")
        assert json.loads(ws.receive_text()) == {"type": "error", "data": {"message": "parse_error"}}

    assert any(event["type"] == "parse_error" for event in events())


def test_ws_missing_type_returns_protocol_error(client, events):
    with client.websocket_connect("/ws") as ws:
        ws.send_text(json.dumps({"data": {"value": 1}}))
        assert json.loads(ws.receive_text()) == {"type": "error", "data": {"message": "protocol_error"}}

    assert any(event["type"] == "protocol_error" for event in events())


def test_debug_ws_send_no_socket_returns_409(client):
    response = client.post("/debug/ws/send", json={"type": "rpc.call", "data": {"method": "pay"}})
    assert response.status_code == 409
    body = response.json()
    assert body["code"] != 0
    assert "未连接" in body["msg"]


def test_debug_ws_send_allowed_type_returns_200_and_delivers(client, events):
    with client.websocket_connect("/ws") as ws:
        ws.send_text(json.dumps({"type": "register", "data": {"userId": "test"}}))
        ws.receive_text()

        envelope = {"type": "rpc.call", "data": {"method": "check_bill", "args": {}}}
        response = client.post("/debug/ws/send", json=envelope)
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0

        received = json.loads(ws.receive_text())
        assert received == envelope

    out_events = [
        e
        for e in events()
        if e["transport"] == "ws" and e["direction"] == "out" and e["type"] == "rpc.call"
    ]
    assert len(out_events) == 1
    assert out_events[0]["payload"] == envelope


def test_debug_ws_send_unknown_type_returns_400(client):
    response = client.post("/debug/ws/send", json={"type": "unknown.type", "data": {}})
    assert response.status_code == 400
    body = response.json()
    assert body["code"] != 0
    assert "不支持" in body["msg"]


def test_two_devices_with_different_users_coexist(client, events):
    with client.websocket_connect("/ws") as ws1:
        ws1.send_text(json.dumps({"type": "register", "data": {"userId": "alice"}}))
        ws1.receive_text()
        with client.websocket_connect("/ws") as ws2:
            ws2.send_text(json.dumps({"type": "register", "data": {"userId": "bob"}}))
            ws2.receive_text()

            response = client.post(
                "/debug/ws/send",
                json={"type": "rpc.call", "data": {"m": 1}, "userId": "alice"},
            )
            assert response.status_code == 200
            received = json.loads(ws1.receive_text())
            assert received["data"]["m"] == 1

            response = client.post(
                "/debug/ws/send",
                json={"type": "rpc.call", "data": {"m": 2}, "userId": "bob"},
            )
            assert response.status_code == 200
            received = json.loads(ws2.receive_text())
            assert received["data"]["m"] == 2


def test_same_user_reconnect_replaces_old_socket(client):
    with client.websocket_connect("/ws") as ws1:
        ws1.send_text(json.dumps({"type": "register", "data": {"userId": "alice"}}))
        ws1.receive_text()
        with client.websocket_connect("/ws") as ws2:
            ws2.send_text(json.dumps({"type": "register", "data": {"userId": "alice"}}))
            ws2.receive_text()
            with pytest.raises(WebSocketDisconnect):
                ws1.receive_text()


def test_broadcast_without_userid_reaches_all_devices(client):
    with client.websocket_connect("/ws") as ws1:
        ws1.send_text(json.dumps({"type": "register", "data": {"userId": "alice"}}))
        ws1.receive_text()
        with client.websocket_connect("/ws") as ws2:
            ws2.send_text(json.dumps({"type": "register", "data": {"userId": "bob"}}))
            ws2.receive_text()

            response = client.post(
                "/debug/ws/send",
                json={"type": "rpc.call", "data": {"broadcast": True}},
            )
            assert response.status_code == 200
            assert json.loads(ws1.receive_text())["data"]["broadcast"] is True
            assert json.loads(ws2.receive_text())["data"]["broadcast"] is True


def test_send_to_unknown_userid_returns_409(client):
    with client.websocket_connect("/ws") as ws:
        ws.send_text(json.dumps({"type": "register", "data": {"userId": "alice"}}))
        ws.receive_text()

        response = client.post(
            "/debug/ws/send",
            json={"type": "rpc.call", "data": {}, "userId": "nobody"},
        )
        assert response.status_code == 409


def test_ws_manager_register_failure_runs_socket_cleanup(client, events):
    manager = client.app.state.ws_manager
    manager.register = AsyncMock(side_effect=RuntimeError("register failed"))
    manager.disconnect = AsyncMock()

    with client.websocket_connect("/ws") as ws:
        ws.send_text(json.dumps({"type": "register", "data": {"userId": "alice"}}))
        with pytest.raises(WebSocketDisconnect):
            ws.receive_text()

    assert manager.disconnect.await_count == 1
    event_types = [event["type"] for event in events()]
    assert "socket_error" in event_types
    assert "disconnected" in event_types
