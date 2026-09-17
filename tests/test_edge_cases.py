import pytest

from order_desk.util.text import (
    InvalidCustomerNameError,
    InvalidPhoneError,
    validate_customer_name,
    validate_phone,
)


def _create_customer(client, name="Jane Doe", phone="555-0100"):
    res = client.post("/api/v1/customers/get-or-create", json={"name": name, "phone": phone})
    assert res.status_code == 200, res.text
    return res.json()


@pytest.mark.parametrize(
    "name,expected_fragment",
    [
        ("A", "at least 2"),
        ("12345", "numbers only"),
        ("!!!", "letter"),
        ("   ", "at least 2"),
        ("1", "at least 2"),
    ],
)
def test_customer_name_rejected(client, name, expected_fragment):
    res = client.post(
        "/api/v1/customers/get-or-create",
        json={"name": name, "phone": "555-0100"},
    )
    assert res.status_code == 400
    assert expected_fragment.lower() in res.json()["detail"].lower()


def test_customer_name_numbers_with_letters_accepted(client):
    created = _create_customer(client, name="Unit 42A", phone="555-0111")
    assert created["name"] == "Unit 42A"


def test_customer_name_whitespace_collapsed(client):
    created = _create_customer(client, name="  Jane   Doe  ", phone="555-0112")
    assert created["name"] == "Jane Doe"


@pytest.mark.parametrize(
    "phone,expected_fragment",
    [
        ("12345", "at least 7"),
        ("abcdefghi", "at least 7"),
        ("1234567890123456", "at most 15"),
    ],
)
def test_phone_rejected(client, phone, expected_fragment):
    res = client.post(
        "/api/v1/customers/get-or-create",
        json={"name": "Jane Doe", "phone": phone},
    )
    assert res.status_code == 400
    assert expected_fragment.lower() in res.json()["detail"].lower()


def test_invalid_garment_type_rejected(client):
    customer = _create_customer(client, phone="555-0200")
    cid = customer["id"]
    inv = client.post(
        "/api/v1/invoices",
        json={"customer_id": cid, "invoice_number": "0001"},
    )
    assert inv.status_code == 201

    res = client.post(
        "/api/v1/garments",
        json={
            "customer_id": cid,
            "invoice_number": "0001",
            "garment_type": "Tuxedo",
            "status": "received",
        },
    )
    assert res.status_code == 400
    assert "invalid garment type" in res.json()["detail"].lower()


def test_invalid_customer_id_on_invoice(client):
    res = client.post(
        "/api/v1/invoices",
        json={"customer_id": 0, "invoice_number": "5002"},
    )
    assert res.status_code == 422


def test_invalid_customer_id_on_garment(client):
    res = client.post(
        "/api/v1/garments",
        json={
            "customer_id": -1,
            "invoice_number": "5003",
            "garment_type": "Suit",
            "status": "received",
        },
    )
    assert res.status_code == 422


def test_whitespace_invoice_number_rejected(client):
    customer = _create_customer(client, phone="555-0300")
    res = client.post(
        "/api/v1/invoices",
        json={"customer_id": customer["id"], "invoice_number": "   "},
    )
    assert res.status_code == 400
    assert "required" in res.json()["detail"].lower() or "digits" in res.json()["detail"].lower()


def test_validate_customer_name_unit():
    assert validate_customer_name("Jane Doe") == "Jane Doe"
    assert validate_customer_name("  Bob   Lee  ") == "Bob Lee"
    with pytest.raises(InvalidCustomerNameError):
        validate_customer_name("X")
    with pytest.raises(InvalidCustomerNameError):
        validate_customer_name("99999")


def test_validate_phone_max_digits():
    with pytest.raises(InvalidPhoneError):
        validate_phone("1" * 16)
