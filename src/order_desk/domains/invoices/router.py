from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from order_desk.auth import OperatorContext, require_operator
from order_desk.db.session import get_db
from order_desk.domains.invoices.schemas import InvoiceCreate, InvoiceRead
from order_desk.domains.invoices.service import InvoiceService, InvoiceServiceError

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.post("", response_model=InvoiceRead, status_code=201)
def create_invoice(
    payload: InvoiceCreate,
    db: Session = Depends(get_db),
    _operator: OperatorContext = Depends(require_operator),
) -> InvoiceRead:
    try:
        return InvoiceService(db).create(payload)
    except InvoiceServiceError as exc:
        status_code = 409 if "already exists" in str(exc).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.get("/next-number")
def next_invoice_number(db: Session = Depends(get_db)) -> dict[str, str]:
    return {"invoice_number": InvoiceService(db).next_number()}


@router.get("/by-customer/{customer_id}", response_model=list[InvoiceRead])
def list_invoices(customer_id: int, db: Session = Depends(get_db)) -> list[InvoiceRead]:
    try:
        return InvoiceService(db).list_for_customer(customer_id)
    except InvoiceServiceError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
