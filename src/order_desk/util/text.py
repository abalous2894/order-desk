"""Shared text helpers for safe query handling."""

INVOICE_NUMBER_WIDTH = 4


class InvalidInvoiceNumberError(ValueError):
    pass


class InvalidPhoneError(ValueError):
    pass


class InvalidCustomerNameError(ValueError):
    pass


MIN_PHONE_DIGITS = 7
MAX_PHONE_DIGITS = 15
MIN_NAME_LENGTH = 2
MAX_NAME_LENGTH = 200


def normalize_phone(value: str) -> str:
    """Keep digits and leading + only."""
    return "".join(ch for ch in value.strip() if ch.isdigit() or ch == "+")


def validate_phone(value: str) -> str:
    normalized = normalize_phone(value)
    digit_count = sum(ch.isdigit() for ch in normalized)
    if digit_count < MIN_PHONE_DIGITS:
        raise InvalidPhoneError(
            f"Phone must contain at least {MIN_PHONE_DIGITS} digits (for example 5550100)"
        )
    if digit_count > MAX_PHONE_DIGITS:
        raise InvalidPhoneError(
            f"Phone must contain at most {MAX_PHONE_DIGITS} digits"
        )
    return normalized


def validate_customer_name(value: str) -> str:
    collapsed = " ".join(value.split())
    if len(collapsed) < MIN_NAME_LENGTH:
        raise InvalidCustomerNameError(
            f"Customer name must be at least {MIN_NAME_LENGTH} characters"
        )
    if len(collapsed) > MAX_NAME_LENGTH:
        raise InvalidCustomerNameError(
            f"Customer name must be at most {MAX_NAME_LENGTH} characters"
        )
    if collapsed.isdigit():
        raise InvalidCustomerNameError("Customer name cannot be numbers only")
    if not any(ch.isalpha() for ch in collapsed):
        raise InvalidCustomerNameError("Customer name must contain at least one letter")
    return collapsed


def invoice_sequence_int(invoice_number: str) -> int:
    """Return the numeric ticket sequence (0006 -> 6)."""
    return int(invoice_number.lstrip("0") or "0")


def normalize_invoice_number(value: str) -> str:
    """Canonicalize numeric ticket numbers so 5, 05, and 000000001 resolve to the same invoice."""
    cleaned = value.strip().upper()
    if not cleaned:
        raise InvalidInvoiceNumberError("Invoice number is required")
    if not cleaned.isdigit():
        raise InvalidInvoiceNumberError(
            "Invoice number must contain digits only (for example 0005)"
        )
    canonical = str(int(cleaned))
    if len(canonical) <= INVOICE_NUMBER_WIDTH:
        return canonical.zfill(INVOICE_NUMBER_WIDTH)
    return canonical


def escape_like(value: str) -> str:
    """Escape SQL LIKE wildcards so user input is matched literally."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
