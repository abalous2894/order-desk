from sqlalchemy import select
from sqlalchemy.orm import Session

from order_desk.domains.invoices.models import InvoiceORM
from order_desk.util.text import invoice_sequence_int, normalize_invoice_number


class InvoiceRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, customer_id: int, invoice_number: str) -> InvoiceORM:
        row = InvoiceORM(
            customer_id=customer_id,
            invoice_number=normalize_invoice_number(invoice_number),
        )
        self.db.add(row)
        self.db.flush()
        return row

    def get_by_number(self, invoice_number: str) -> InvoiceORM | None:
        stmt = select(InvoiceORM).where(
            InvoiceORM.invoice_number == normalize_invoice_number(invoice_number)
        )
        return self.db.scalar(stmt)

    def first_missing_prior_sequence(self, target_seq: int) -> int | None:
        if target_seq <= 1:
            return None
        stmt = select(InvoiceORM.invoice_number)
        existing = {invoice_sequence_int(number) for number in self.db.scalars(stmt)}
        for seq in range(1, target_seq):
            if seq not in existing:
                return seq
        return None

    def next_required_number(self) -> str:
        stmt = select(InvoiceORM.invoice_number)
        numbers = list(self.db.scalars(stmt))
        if not numbers:
            return normalize_invoice_number("1")
        highest = max(invoice_sequence_int(number) for number in numbers)
        return normalize_invoice_number(str(highest + 1))

    def list_for_customer(self, customer_id: int) -> list[InvoiceORM]:
        stmt = (
            select(InvoiceORM)
            .where(InvoiceORM.customer_id == customer_id)
            .order_by(InvoiceORM.created_at.desc())
        )
        return list(self.db.scalars(stmt))
