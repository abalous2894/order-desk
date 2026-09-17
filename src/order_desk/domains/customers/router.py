from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from order_desk.auth import OperatorContext, require_operator
from order_desk.db.session import get_db
from order_desk.domains.customers.schemas import CustomerCreate, CustomerProfile, CustomerRead
from order_desk.domains.customers.service import CustomerService, CustomerServiceError

router = APIRouter(prefix="/customers", tags=["customers"])


@router.post("", response_model=CustomerRead, status_code=201)
def create_customer(
    payload: CustomerCreate,
    db: Session = Depends(get_db),
    _operator: OperatorContext = Depends(require_operator),
) -> CustomerRead:
    try:
        return CustomerService(db).create(payload)
    except CustomerServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/get-or-create", response_model=CustomerRead)
def get_or_create_customer(
    payload: CustomerCreate,
    db: Session = Depends(get_db),
    _operator: OperatorContext = Depends(require_operator),
) -> CustomerRead:
    try:
        return CustomerService(db).get_or_create(payload)
    except CustomerServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/search", response_model=list[CustomerRead])
def search_customers(
    q: str = Query(min_length=1, max_length=100),
    db: Session = Depends(get_db),
) -> list[CustomerRead]:
    return CustomerService(db).search(q)


@router.get("/{customer_id}", response_model=CustomerProfile)
def get_customer(customer_id: int, db: Session = Depends(get_db)) -> CustomerProfile:
    try:
        return CustomerService(db).profile(customer_id)
    except CustomerServiceError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
