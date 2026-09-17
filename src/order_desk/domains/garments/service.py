from sqlalchemy.orm import Session

from order_desk.domains.customers.repository import CustomerRepository
from order_desk.domains.garments.constants import GARMENT_TYPES
from order_desk.domains.garments.audit_repository import GarmentStatusAuditRepository
from order_desk.domains.garments.repository import GarmentRepository
from order_desk.domains.garments.schemas import (
    GarmentCreate,
    GarmentRead,
    GarmentStatusEventRead,
    GarmentStatusUpdate,
)
from order_desk.domains.invoices.repository import InvoiceRepository
from order_desk.domains.status_lifecycle.service import (
    GarmentStatus,
    StatusLifecycleError,
    assert_valid_status,
    assert_valid_transition,
)
from order_desk.util.text import InvalidInvoiceNumberError, normalize_invoice_number


class GarmentServiceError(ValueError):
    pass


class GarmentService:
    def __init__(self, db: Session) -> None:
        self.repo = GarmentRepository(db)
        self.audit = GarmentStatusAuditRepository(db)
        self.invoices = InvoiceRepository(db)
        self.customers = CustomerRepository(db)
        self.db = db

    def create(self, payload: GarmentCreate, *, actor_id: str) -> GarmentRead:
        customer = self.customers.get_by_id(payload.customer_id)
        if not customer:
            raise GarmentServiceError("Customer not found")

        try:
            status = assert_valid_status(payload.status)
        except StatusLifecycleError as exc:
            raise GarmentServiceError(str(exc)) from exc

        try:
            invoice_number = normalize_invoice_number(payload.invoice_number)
        except InvalidInvoiceNumberError as exc:
            raise GarmentServiceError(str(exc)) from exc

        invoice = self.invoices.get_by_number(invoice_number)
        if not invoice:
            raise GarmentServiceError("Invoice not found; create the invoice first")
        if invoice.customer_id != payload.customer_id:
            raise GarmentServiceError("Invoice belongs to a different customer")

        garment_type = payload.garment_type.strip()
        if garment_type not in GARMENT_TYPES:
            allowed = ", ".join(GARMENT_TYPES)
            raise GarmentServiceError(
                f"Invalid garment type {garment_type!r}. Allowed: {allowed}"
            )

        existing = self.repo.list_for_invoice(invoice.id)
        if existing and all(g.status == GarmentStatus.COMPLETED for g in existing):
            raise GarmentServiceError(
                "Invoice is complete. Create a new invoice for additional garments."
            )

        row = self.repo.create(payload.customer_id, invoice.id, garment_type, status)
        self.audit.append(
            garment_id=row.id,
            from_status=None,
            to_status=status,
            actor=actor_id,
        )
        self.db.commit()
        loaded = self.repo.get_by_id(row.id)
        if loaded is None:
            raise GarmentServiceError("Garment was created but could not be reloaded")
        return _to_read(loaded)

    def list_for_customer(self, customer_id: int) -> list[GarmentRead]:
        if not self.customers.get_by_id(customer_id):
            raise GarmentServiceError("Customer not found")
        rows = self.repo.list_for_customer(customer_id)
        return [_to_read(r) for r in rows]

    def update_status(
        self,
        garment_id: int,
        payload: GarmentStatusUpdate,
        *,
        actor_id: str,
    ) -> GarmentRead:
        row = self.repo.get_by_id(garment_id)
        if not row:
            raise GarmentServiceError("Garment not found")
        try:
            new_status = assert_valid_status(payload.status)
            assert_valid_transition(row.status, new_status)
        except StatusLifecycleError as exc:
            raise GarmentServiceError(str(exc)) from exc
        previous_status = row.status
        if previous_status != new_status:
            self.repo.update_status(row, new_status)
            self.audit.append(
                garment_id=row.id,
                from_status=previous_status,
                to_status=new_status,
                actor=actor_id,
            )
        self.db.commit()
        self.db.refresh(row)
        return _to_read(row)

    def list_status_events(self, garment_id: int) -> list[GarmentStatusEventRead]:
        row = self.repo.get_by_id(garment_id)
        if not row:
            raise GarmentServiceError("Garment not found")
        events = self.audit.list_for_garment(garment_id)
        return [GarmentStatusEventRead.model_validate(event) for event in events]


def _to_read(row) -> GarmentRead:
    return GarmentRead(
        id=row.id,
        customer_id=row.customer_id,
        invoice_id=row.invoice_id,
        invoice_number=row.invoice.invoice_number,
        garment_type=row.garment_type,
        status=row.status,
    )
