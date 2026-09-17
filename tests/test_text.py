import pytest

from order_desk.util.text import (
    InvalidCustomerNameError,
    InvalidInvoiceNumberError,
    InvalidPhoneError,
    escape_like,
    invoice_sequence_int,
    normalize_invoice_number,
    validate_customer_name,
    validate_phone,
)


def test_escape_like_percent_and_underscore():
    assert escape_like("100%_off") == "100\\%\\_off"


def test_invoice_sequence_int():
    assert invoice_sequence_int("0001") == 1
    assert invoice_sequence_int("0006") == 6
    assert invoice_sequence_int("7101") == 7101


def test_normalize_invoice_number_numeric_aliases():
    assert normalize_invoice_number("5") == "0005"
    assert normalize_invoice_number("05") == "0005"
    assert normalize_invoice_number("005") == "0005"
    assert normalize_invoice_number("0003") == "0003"
    assert normalize_invoice_number("000000001") == "0001"
    assert normalize_invoice_number("00000001") == "0001"


def test_validate_phone_requires_digits():
    assert validate_phone("555-0100") == "5550100"
    with pytest.raises(InvalidPhoneError):
        validate_phone("abcdefghi")
    with pytest.raises(InvalidPhoneError):
        validate_phone("12345")


def test_normalize_invoice_number_rejects_non_numeric():
    with pytest.raises(InvalidInvoiceNumberError):
        normalize_invoice_number("000A")
    with pytest.raises(InvalidInvoiceNumberError):
        normalize_invoice_number("INV-1001")
    with pytest.raises(InvalidInvoiceNumberError):
        normalize_invoice_number("   ")


def test_validate_customer_name_rules():
    assert validate_customer_name("Jane Doe") == "Jane Doe"
    with pytest.raises(InvalidCustomerNameError):
        validate_customer_name("A")
    with pytest.raises(InvalidCustomerNameError):
        validate_customer_name("123456")
    with pytest.raises(InvalidCustomerNameError):
        validate_customer_name("---")
