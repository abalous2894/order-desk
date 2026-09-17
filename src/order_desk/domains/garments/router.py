from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from order_desk.auth import OperatorContext, require_operator
from order_desk.db.session import get_db
from order_desk.domains.garments.schemas import (
    GarmentCreate,
    GarmentRead,
    GarmentStatusEventRead,
    GarmentStatusUpdate,
)
from order_desk.domains.garments.service import GarmentService, GarmentServiceError
from order_desk.domains.status_lifecycle.service import GARMENT_STATUSES

router = APIRouter(prefix="/garments", tags=["garments"])


@router.get("/statuses", response_model=list[str])
def list_statuses() -> list[str]:
    return list(GARMENT_STATUSES)


@router.post("", response_model=GarmentRead, status_code=201)
def create_garment(
    payload: GarmentCreate,
    db: Session = Depends(get_db),
    operator: OperatorContext = Depends(require_operator),
) -> GarmentRead:
    try:
        return GarmentService(db).create(payload, actor_id=operator.actor_id)
    except GarmentServiceError as exc:
        message = str(exc)
        status_code = 409 if message.startswith("Invoice is complete") else 400
        raise HTTPException(status_code=status_code, detail=message) from exc


@router.get("/by-customer/{customer_id}", response_model=list[GarmentRead])
def list_garments(customer_id: int, db: Session = Depends(get_db)) -> list[GarmentRead]:
    try:
        return GarmentService(db).list_for_customer(customer_id)
    except GarmentServiceError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{garment_id}/status-events", response_model=list[GarmentStatusEventRead])
def list_garment_status_events(
    garment_id: int,
    db: Session = Depends(get_db),
    _operator: OperatorContext = Depends(require_operator),
) -> list[GarmentStatusEventRead]:
    try:
        return GarmentService(db).list_status_events(garment_id)
    except GarmentServiceError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/{garment_id}/status", response_model=GarmentRead)
def update_garment_status(
    garment_id: int,
    payload: GarmentStatusUpdate,
    db: Session = Depends(get_db),
    operator: OperatorContext = Depends(require_operator),
) -> GarmentRead:
    try:
        return GarmentService(db).update_status(
            garment_id,
            payload,
            actor_id=operator.actor_id,
        )
    except GarmentServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
