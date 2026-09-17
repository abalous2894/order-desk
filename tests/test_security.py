def test_search_rejects_overlong_query(client):
    res = client.get("/api/v1/customers/search", params={"q": "x" * 101})
    assert res.status_code == 422


def test_search_sql_injection_literal(client):
    client.post(
        "/api/v1/customers/get-or-create",
        json={"name": "Safe Name", "phone": "555-9001"},
    )
    res = client.get("/api/v1/customers/search", params={"q": "'; DROP TABLE customers; --"})
    assert res.status_code == 200
    assert res.json() == []


def test_search_percent_wildcard_is_literal(client):
    client.post(
        "/api/v1/customers/get-or-create",
        json={"name": "Percent User", "phone": "555-9002"},
    )
    res = client.get("/api/v1/customers/search", params={"q": "%"})
    assert res.status_code == 200
    assert res.json() == []


def test_get_or_create_rejects_name_mismatch_for_phone(client):
    client.post(
        "/api/v1/customers/get-or-create",
        json={"name": "Original Name", "phone": "555-9003"},
    )
    res = client.post(
        "/api/v1/customers/get-or-create",
        json={"name": "Different Name", "phone": "555-9003"},
    )
    assert res.status_code == 400


def test_invalid_garment_status_on_create(client):
    customer = client.post(
        "/api/v1/customers/get-or-create",
        json={"name": "Status Test", "phone": "555-9004"},
    ).json()
    client.post(
        "/api/v1/invoices",
        json={"customer_id": customer["id"], "invoice_number": "0001"},
    )
    res = client.post(
        "/api/v1/garments",
        json={
            "customer_id": customer["id"],
            "invoice_number": "0001",
            "garment_type": "Suit",
            "status": "lost",
        },
    )
    assert res.status_code == 400


def test_health_endpoint(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["ok"] == "true"
