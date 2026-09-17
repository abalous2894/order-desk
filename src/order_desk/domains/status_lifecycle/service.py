"""Garment status lifecycle rules (domain module, no HTTP/ORM)."""

from enum import StrEnum


class GarmentStatus(StrEnum):
    RECEIVED = "received"
    IN_PROGRESS = "in_progress"
    READY_FOR_PICKUP = "ready_for_pickup"
    COMPLETED = "completed"


GARMENT_STATUSES = tuple(s.value for s in GarmentStatus)
_STATUS_ORDER = {status: index for index, status in enumerate(GARMENT_STATUSES)}


def _order_by_lifecycle(statuses: set[str] | list[str]) -> list[str]:
    return sorted(statuses, key=lambda s: _STATUS_ORDER[s])


# Allowed forward transitions; completed is terminal
_TRANSITIONS: dict[str, set[str]] = {
    GarmentStatus.RECEIVED: {GarmentStatus.IN_PROGRESS, GarmentStatus.READY_FOR_PICKUP},
    GarmentStatus.IN_PROGRESS: {GarmentStatus.READY_FOR_PICKUP, GarmentStatus.COMPLETED},
    GarmentStatus.READY_FOR_PICKUP: {GarmentStatus.COMPLETED},
    GarmentStatus.COMPLETED: set(),
}


class StatusLifecycleError(ValueError):
    pass


def assert_valid_status(status: str) -> str:
    normalized = status.strip().lower().replace(" ", "_")
    if normalized not in GARMENT_STATUSES:
        raise StatusLifecycleError(
            f"Invalid status {status!r}. Allowed: {', '.join(GARMENT_STATUSES)}"
        )
    return normalized


def allowed_next_statuses(current: str) -> list[str]:
    """Current status plus valid forward targets for UI dropdowns."""
    current_n = assert_valid_status(current)
    return [current_n, *_order_by_lifecycle(_TRANSITIONS[current_n])]


def transition_rules() -> dict[str, list[str]]:
    return {status: _order_by_lifecycle(_TRANSITIONS[status]) for status in GARMENT_STATUSES}


def assert_valid_transition(current: str, new: str) -> None:
    current_n = assert_valid_status(current)
    new_n = assert_valid_status(new)
    if current_n == new_n:
        return
    allowed = _TRANSITIONS[current_n]
    if new_n not in allowed:
        raise StatusLifecycleError(
            f"Cannot transition from {current_n!r} to {new_n!r}. "
            f"Allowed next: {', '.join(_order_by_lifecycle(allowed)) or '(terminal)'}"
        )
