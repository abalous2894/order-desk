from conftest import AUTH_HEADERS


def _setup_garment(client):
    customer = client.post(
        "/api/v1/customers/get-or-create",
        json={"name": "Audit User", "phone": "555-8800"},
        headers=AUTH_HEADERS,
    ).json()
    client.post(
        "/api/v1/invoices",
        json={"customer_id": customer["id"], "invoice_number": "0001"},
        headers=AUTH_HEADERS,
    )
    garment = client.post(
        "/api/v1/garments",
        json={
            "customer_id": customer["id"],
            "invoice_number": "0001",
            "garment_type": "Suit",
            "status": "received",
        },
        headers=AUTH_HEADERS,
    ).json()
    return garment


def test_garment_create_writes_initial_audit_event(client):
    garment = _setup_garment(client)
    events = client.get(
        f"/api/v1/garments/{garment['id']}/status-events",
        headers=AUTH_HEADERS,
    ).json()
    assert len(events) == 1
    assert events[0]["from_status"] is None
    assert events[0]["to_status"] == "received"
    assert events[0]["actor"] == "AUDIT01"


def test_status_update_appends_audit_event(client):
    garment = _setup_garment(client)
    client.patch(
        f"/api/v1/garments/{garment['id']}/status",
        json={"status": "in_progress"},
        headers={**AUTH_HEADERS, "X-Operator-Id": "CLERK02"},
    )
    events = client.get(
        f"/api/v1/garments/{garment['id']}/status-events",
        headers=AUTH_HEADERS,
    ).json()
    assert len(events) == 2
    assert events[1]["from_status"] == "received"
    assert events[1]["to_status"] == "in_progress"
    assert events[1]["actor"] == "CLERK02"


def test_status_events_accumulate_in_order(client):
    garment = _setup_garment(client)
    for status in ("in_progress", "ready_for_pickup", "completed"):
        client.patch(
            f"/api/v1/garments/{garment['id']}/status",
            json={"status": status},
            headers=AUTH_HEADERS,
        )
    events = client.get(
        f"/api/v1/garments/{garment['id']}/status-events",
        headers=AUTH_HEADERS,
    ).json()
    assert len(events) == 4
    assert events[0]["to_status"] == "received"
    assert events[-1]["to_status"] == "completed"
    assert events[0]["id"] < events[-1]["id"]


def test_status_events_require_auth(bare_client, client):
    garment = _setup_garment(client)
    res = bare_client.get(f"/api/v1/garments/{garment['id']}/status-events")
    assert res.status_code == 401
