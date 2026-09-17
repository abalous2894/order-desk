def _create_customer(client, name="Jane Doe", phone="555-0100"):
    res = client.post("/api/v1/customers/get-or-create", json={"name": name, "phone": phone})
    assert res.status_code == 200
    return res.json()


def _create_invoice(client, customer_id, invoice_number="1"):
    res = client.post(
        "/api/v1/invoices",
        json={"customer_id": customer_id, "invoice_number": invoice_number},
    )
    assert res.status_code == 201, res.text
    return res.json()


def _create_garment(client, customer_id, invoice_number, garment_type="Suit", status="received"):
    res = client.post(
        "/api/v1/garments",
        json={
            "customer_id": customer_id,
            "invoice_number": invoice_number,
            "garment_type": garment_type,
            "status": status,
        },
    )
    assert res.status_code == 201
    return res.json()


def test_customer_one_to_many_invoices_and_garments(client):
    customer = _create_customer(client)
    cid = customer["id"]

    _create_invoice(client, cid, "0001")
    _create_invoice(client, cid, "0002")
    _create_garment(client, cid, "0001", "Suit")
    _create_garment(client, cid, "0001", "Shirt")
    _create_garment(client, cid, "0002", "Dress")

    profile = client.get(f"/api/v1/customers/{cid}").json()
    assert profile["invoice_count"] == 2
    assert profile["garment_count"] == 3

    garments = client.get(f"/api/v1/garments/by-customer/{cid}").json()
    assert len(garments) == 3
    assert {g["invoice_number"] for g in garments} == {"0001", "0002"}


def test_invalid_phone_rejected(client):
    res = client.post(
        "/api/v1/customers/get-or-create",
        json={"name": "Andrew Balous", "phone": "abcdefghi"},
    )
    assert res.status_code == 400
    assert "digits" in res.json()["detail"].lower()


def test_customer_composite_unique_enforced(client):
    _create_customer(client, name="Alice", phone="555-0200")
    dup = client.post(
        "/api/v1/customers",
        json={"name": "Alice", "phone": "555-0200"},
    )
    assert dup.status_code == 400


def test_phone_lookup_and_search(client):
    created = _create_customer(client, name="Bob Smith", phone="555-0300")
    by_phone = client.get("/api/v1/customers/search?q=555-0300").json()
    assert len(by_phone) == 1
    assert by_phone[0]["id"] == created["id"]

    by_name = client.get("/api/v1/customers/search?q=Bob").json()
    assert any(row["id"] == created["id"] for row in by_name)


def test_get_or_create_idempotent(client):
    first = _create_customer(client, name="Carol", phone="555-0400")
    second = client.post(
        "/api/v1/customers/get-or-create",
        json={"name": "Carol", "phone": "555-0400"},
    ).json()
    assert second["id"] == first["id"]


def test_invoice_numeric_aliases_are_same_number(client):
    customer = _create_customer(client, name="Norm", phone="555-0550")
    created = _create_invoice(client, customer["id"], "000000001")
    assert created["invoice_number"] == "0001"
    for alias in ("1", "01", "0001", "00000001"):
        conflict = client.post(
            "/api/v1/invoices",
            json={"customer_id": customer["id"], "invoice_number": alias},
        )
        assert conflict.status_code == 409


def test_invoice_five_aliases_are_same_number(client):
    customer = _create_customer(client, name="Norma", phone="555-0551")
    for n in ("1", "2", "3", "4"):
        _create_invoice(client, customer["id"], n)
    created = _create_invoice(client, customer["id"], "005")
    assert created["invoice_number"] == "0005"
    for alias in ("5", "05", "0005", "000000005"):
        conflict = client.post(
            "/api/v1/invoices",
            json={"customer_id": customer["id"], "invoice_number": alias},
        )
        assert conflict.status_code == 409


def test_invalid_invoice_number_rejected(client):
    customer = _create_customer(client, name="Invalid", phone="555-0555")
    res = client.post(
        "/api/v1/invoices",
        json={"customer_id": customer["id"], "invoice_number": "000A"},
    )
    assert res.status_code == 400
    assert "digits only" in res.json()["detail"].lower()


def test_invoice_number_unique_globally(client):
    c1 = _create_customer(client, name="Dan", phone="555-0501")
    c2 = _create_customer(client, name="Eve", phone="555-0502")
    _create_invoice(client, c1["id"], "0001")
    conflict = client.post(
        "/api/v1/invoices",
        json={"customer_id": c2["id"], "invoice_number": "0001"},
    )
    assert conflict.status_code == 409


def test_invoice_sequence_enforced(client):
    customer = _create_customer(client, name="Seq", phone="555-0503")
    skipped = client.post(
        "/api/v1/invoices",
        json={"customer_id": customer["id"], "invoice_number": "0006"},
    )
    assert skipped.status_code == 400
    assert "0001" in skipped.json()["detail"]

    _create_invoice(client, customer["id"], "0001")
    still_skipped = client.post(
        "/api/v1/invoices",
        json={"customer_id": customer["id"], "invoice_number": "0006"},
    )
    assert still_skipped.status_code == 400
    assert "0002" in still_skipped.json()["detail"]

    _create_invoice(client, customer["id"], "0002")
    ok = client.post(
        "/api/v1/invoices",
        json={"customer_id": customer["id"], "invoice_number": "0003"},
    )
    assert ok.status_code == 201


def test_next_invoice_number_endpoint(client):
    assert client.get("/api/v1/invoices/next-number").json() == {"invoice_number": "0001"}
    customer = _create_customer(client, name="Next", phone="555-0504")
    _create_invoice(client, customer["id"], "0001")
    assert client.get("/api/v1/invoices/next-number").json() == {"invoice_number": "0002"}


def test_garment_requires_existing_invoice(client):
    customer = _create_customer(client, name="Frank", phone="555-0600")
    missing = client.post(
        "/api/v1/garments",
        json={
            "customer_id": customer["id"],
            "invoice_number": "0001",
            "garment_type": "Coat",
            "status": "received",
        },
    )
    assert missing.status_code == 400


def test_garment_invoice_must_belong_to_same_customer(client):
    c1 = _create_customer(client, name="Grace", phone="555-0701")
    c2 = _create_customer(client, name="Henry", phone="555-0702")
    _create_invoice(client, c1["id"], "0001")

    wrong = client.post(
        "/api/v1/garments",
        json={
            "customer_id": c2["id"],
            "invoice_number": "0001",
            "garment_type": "Pants",
            "status": "received",
        },
    )
    assert wrong.status_code == 400


def test_cannot_add_garment_to_completed_invoice(client):
    customer = _create_customer(client, name="Jack", phone="555-0850")
    _create_invoice(client, customer["id"], "0001")
    garment = _create_garment(client, customer["id"], "0001")
    for status in ("in_progress", "ready_for_pickup", "completed"):
        client.patch(
            f"/api/v1/garments/{garment['id']}/status",
            json={"status": status},
        )
    conflict = client.post(
        "/api/v1/garments",
        json={
            "customer_id": customer["id"],
            "invoice_number": "0001",
            "garment_type": "Coat",
            "status": "received",
        },
    )
    assert conflict.status_code == 409


def test_status_lifecycle_enforced_on_update(client):
    customer = _create_customer(client, name="Ivy", phone="555-0800")
    _create_invoice(client, customer["id"], "0001")
    garment = _create_garment(client, customer["id"], "0001")

    ok = client.patch(
        f"/api/v1/garments/{garment['id']}/status",
        json={"status": "in_progress"},
    )
    assert ok.status_code == 200

    bad = client.patch(
        f"/api/v1/garments/{garment['id']}/status",
        json={"status": "received"},
    )
    assert bad.status_code == 400
