from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from order_desk.domains.garments.models import GarmentORM


class GarmentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        customer_id: int,
        invoice_id: int,
        garment_type: str,
        status: str,
    ) -> GarmentORM:
        row = GarmentORM(
            customer_id=customer_id,
            invoice_id=invoice_id,
            garment_type=garment_type.strip(),
            status=status,
        )
        self.db.add(row)
        self.db.flush()
        return row

    def get_by_id(self, garment_id: int) -> GarmentORM | None:
        stmt = (
            select(GarmentORM)
            .options(joinedload(GarmentORM.invoice))
            .where(GarmentORM.id == garment_id)
        )
        return self.db.scalar(stmt)

    def list_for_invoice(self, invoice_id: int) -> list[GarmentORM]:
        stmt = select(GarmentORM).where(GarmentORM.invoice_id == invoice_id)
        return list(self.db.scalars(stmt))

    def list_for_customer(self, customer_id: int) -> list[GarmentORM]:
        stmt = (
            select(GarmentORM)
            .options(joinedload(GarmentORM.invoice))
            .where(GarmentORM.customer_id == customer_id)
            .order_by(GarmentORM.id.desc())
        )
        return list(self.db.scalars(stmt))

    def update_status(self, garment: GarmentORM, status: str) -> GarmentORM:
        garment.status = status
        self.db.flush()
        return garment
