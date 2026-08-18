def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    assert body["data"]["status"] == "ok"


def test_all_reporting_routes_accept_and_log_complete_json(client, events):
    cases = [
        ("/api/device/upload_order", {"user": "local-user", "pay_order": "order-1", "pay_id": "pay-1", "amount": 1.25}),
        ("/api/device/upload_sdk", {"pay_id": "pay-1", "sdk_param": "sdk-value"}),
        ("/api/device/mark_paid", {"pay_id": "pay-1"}),
    ]

    for route, payload in cases:
        response = client.post(route, json=payload)
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["msg"] == "成功"

    inbound = [event for event in events() if event["transport"] == "http" and event["direction"] == "in"]
    assert [(event["type"], event["payload"]) for event in inbound] == cases


def test_malformed_json_returns_400_and_is_logged(client, events):
    response = client.post(
        "/api/device/upload_order",
        content=b"not-json",
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 400
    body = response.json()
    assert body["code"] != 0
    assert "参数" in body["msg"]

    rejected = [e for e in events() if e["transport"] == "http" and e["direction"] == "in"]
    assert len(rejected) == 1
    assert rejected[0]["type"] == "/api/device/upload_order"
    assert rejected[0]["payload"]["rejected"] is True
    assert rejected[0]["payload"]["body"] == "not-json"


def test_field_validation_returns_400_and_is_logged(client, events):
    response = client.post(
        "/api/device/upload_order",
        json={"pay_order": "order-1", "pay_id": "pay-1", "amount": "not-a-number"},
    )

    assert response.status_code == 400
    body = response.json()
    assert body["code"] != 0
    assert "参数" in body["msg"]
    rejected = [e for e in events() if e["transport"] == "http" and e["direction"] == "in"]
    assert len(rejected) == 1
    assert rejected[0]["payload"]["rejected"] is True
    assert rejected[0]["payload"]["body"]["pay_id"] == "pay-1"
