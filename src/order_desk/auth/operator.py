"""Operator authentication for mutating API requests."""

from dataclasses import dataclass
from typing import Annotated
import secrets

from fastapi import Header, HTTPException

from order_desk.config import settings


@dataclass(frozen=True)
class OperatorContext:
    actor_id: str


def _extract_bearer(authorization: str | None) -> str | None:
    if not authorization:
        return None
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    token = parts[1].strip()
    return token or None


def require_operator(
    authorization: Annotated[str | None, Header()] = None,
    x_operator_id: Annotated[str | None, Header(alias="X-Operator-Id")] = None,
) -> OperatorContext:
    if not settings.operator_token:
        raise HTTPException(status_code=503, detail="Operator authentication is not configured")

    token = _extract_bearer(authorization)
    if not token or not secrets.compare_digest(token, settings.operator_token):
        raise HTTPException(status_code=401, detail="Invalid or missing operator credentials")

    actor = (x_operator_id or "").strip()
    if len(actor) < 2 or len(actor) > 64:
        raise HTTPException(
            status_code=400,
            detail="X-Operator-Id header is required (2-64 characters)",
        )
    return OperatorContext(actor_id=actor)
