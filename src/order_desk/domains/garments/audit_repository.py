from sqlalchemy import select
from sqlalchemy.orm import Session

from order_desk.domains.garments.audit_models import GarmentStatusEventORM


class GarmentStatusAuditRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def append(
        self,
        *,
        garment_id: int,
        from_status: str | None,
        to_status: str,
        actor: str,
    ) -> GarmentStatusEventORM:
        row = GarmentStatusEventORM(
            garment_id=garment_id,
            from_status=from_status,
            to_status=to_status,
            actor=actor,
        )
        self.db.add(row)
        self.db.flush()
        return row

    def list_for_garment(self, garment_id: int) -> list[GarmentStatusEventORM]:
        stmt = (
            select(GarmentStatusEventORM)
            .where(GarmentStatusEventORM.garment_id == garment_id)
            .order_by(GarmentStatusEventORM.created_at.asc(), GarmentStatusEventORM.id.asc())
        )
        return list(self.db.scalars(stmt))
