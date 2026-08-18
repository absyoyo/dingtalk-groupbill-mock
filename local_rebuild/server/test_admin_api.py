import json

ADMIN_DEVICE = {"userId": "admin-user", "accountId": "admin-org", "clientId": "uid-admin-user"}


def test_devices_lists_registered_devices(client):
    with client.websocket_connect("/ws") as ws:
        ws.send_text(json.dumps({"type": "register", "data": ADMIN_DEVICE}))
        ws.receive_text()

        response = client.get("/api/admin/devices")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        devices = body["data"]["devices"]
        assert len(devices) == 1
        device = devices[0]
        assert device["userId"] == "admin-user"
        assert device["accountId"] == "admin-org"
        assert device["connectedAt"] > 0


def test_events_pagination_and_type_filter(client, event_path):
    client.post("/api/device/upload_order", json={"user": "u", "pay_order": "o", "pay_id": "p", "amount": 1.0})
    response = client.get("/api/admin/events", params={"type": "/api/device/upload_order"})
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    data = body["data"]
    assert data["total"] >= 1
    assert all(e["type"] == "/api/device/upload_order" for e in data["items"])


def test_orders_endpoint_returns_upload_order_records(client):
    client.post("/api/device/upload_order", json={"user": "u2", "pay_order": "o2", "pay_id": "p2", "amount": 2.0})
    response = client.get("/api/admin/orders")
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    assert any(o["payload"]["user"] == "u2" for o in body["data"]["items"])


def test_admin_send_targets_device(client):
    with client.websocket_connect("/ws") as ws:
        ws.send_text(json.dumps({"type": "register", "data": ADMIN_DEVICE}))
        ws.receive_text()

        response = client.post(
            "/api/admin/send",
            json={"type": "bill.task", "data": {"taskId": "x"}, "userId": "admin-user"},
        )
        assert response.status_code == 200
        received = json.loads(ws.receive_text())
        assert received == {"type": "bill.task", "data": {"taskId": "x"}}


def test_kick_removes_device(client):
    with client.websocket_connect("/ws") as ws:
        ws.send_text(json.dumps({"type": "register", "data": ADMIN_DEVICE}))
        ws.receive_text()

        response = client.delete("/api/admin/devices/admin-user")
        assert response.status_code == 200
        listing = client.get("/api/admin/devices").json()
        assert listing["data"]["devices"] == []


def test_console_index_served_when_static_build_exists(client, event_path, tmp_path):
    static_root = tmp_path / "static"
    static_root.mkdir()
    (static_root / "index.html").write_text("<html>console</html>", encoding="utf-8")

    from local_rebuild.server.app import mount_console
    mount_console(client.app, static_root)

    response = client.get("/")
    assert response.status_code == 200
    assert "console" in response.text