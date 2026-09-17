from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from order_desk.domains.customers.repository import CustomerRepository
from order_desk.domains.invoices.repository import InvoiceRepository
from order_desk.domains.invoices.schemas import InvoiceCreate, InvoiceRead
from order_desk.util.text import (
    InvalidInvoiceNumberError,
    invoice_sequence_int,
    normalize_invoice_number,
)


class InvoiceServiceError(ValueError):
    pass


class InvoiceService:
    def __init__(self, db: Session) -> None:
        self.repo = InvoiceRepository(db)
        self.customers = CustomerRepository(db)
        self.db = db

    def create(self, payload: InvoiceCreate) -> InvoiceRead:
        if payload.customer_id <= 0:
            raise InvoiceServiceError("Customer not found")
        if not self.customers.get_by_id(payload.customer_id):
            raise InvoiceServiceError("Customer not found")
        try:
            invoice_number = normalize_invoice_number(payload.invoice_number)
        except InvalidInvoiceNumberError as exc:
            raise InvoiceServiceError(str(exc)) from exc
        if self.repo.get_by_number(invoice_number):
            raise InvoiceServiceError("Invoice number already exists")

        target_seq = invoice_sequence_int(invoice_number)
        missing = self.repo.first_missing_prior_sequence(target_seq)
        if missing is not None:
            prior = normalize_invoice_number(str(missing))
            raise InvoiceServiceError(
                f"Invoice {prior} must exist before creating {invoice_number}"
            )
        try:
            row = self.repo.create(payload.customer_id, invoice_number)
            self.db.commit()
            self.db.refresh(row)
            return InvoiceRead.model_validate(row)
        except IntegrityError as exc:
            self.db.rollback()
            raise InvoiceServiceError("Invoice number already exists") from exc

    def next_number(self) -> str:
        return self.repo.next_required_number()

    def list_for_customer(self, customer_id: int) -> list[InvoiceRead]:
        if not self.customers.get_by_id(customer_id):
            raise InvoiceServiceError("Customer not found")
        rows = self.repo.list_for_customer(customer_id)
        return [InvoiceRead.model_validate(r) for r in rows]
