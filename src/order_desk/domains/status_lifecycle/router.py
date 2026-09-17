from fastapi import APIRouter

from order_desk.domains.status_lifecycle.service import (
    GARMENT_STATUSES,
    allowed_next_statuses,
    transition_rules,
)

router = APIRouter(prefix="/status-lifecycle", tags=["status-lifecycle"])


@router.get("/statuses", response_model=list[str])
def list_statuses() -> list[str]:
    return list(GARMENT_STATUSES)


@router.get("/rules", response_model=dict[str, list[str]])
def list_transition_rules() -> dict[str, list[str]]:
    return transition_rules()


@router.get("/allowed/{current}", response_model=list[str])
def list_allowed_next(current: str) -> list[str]:
    return allowed_next_statuses(current)
