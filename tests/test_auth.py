from conftest import AUTH_HEADERS


def test_mutating_endpoints_require_operator_credentials(bare_client):
    res = bare_client.post(
        "/api/v1/customers/get-or-create",
        json={"name": "Jane Doe", "phone": "555-0100"},
    )
    assert res.status_code == 401


def test_invalid_operator_token_rejected(bare_client):
    res = bare_client.post(
        "/api/v1/customers/get-or-create",
        json={"name": "Jane Doe", "phone": "555-0100"},
        headers={
            "Authorization": "Bearer wrong-token",
            "X-Operator-Id": "AUDIT01",
        },
    )
    assert res.status_code == 401


def test_missing_operator_id_rejected(bare_client):
    res = bare_client.post(
        "/api/v1/customers/get-or-create",
        json={"name": "Jane Doe", "phone": "555-0100"},
        headers={"Authorization": "Bearer test-operator-token"},
    )
    assert res.status_code == 400
    assert "x-operator-id" in res.json()["detail"].lower()


def test_read_endpoints_do_not_require_auth(bare_client):
    res = bare_client.get("/api/v1/customers/search", params={"q": "555"})
    assert res.status_code == 200


def test_authenticated_mutation_succeeds(client):
    res = client.post(
        "/api/v1/customers/get-or-create",
        json={"name": "Jane Doe", "phone": "555-0100"},
        headers=AUTH_HEADERS,
    )
    assert res.status_code == 200
