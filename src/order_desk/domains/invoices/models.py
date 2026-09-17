from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from order_desk.db.base import Base

if TYPE_CHECKING:
    from order_desk.domains.customers.models import CustomerORM
    from order_desk.domains.garments.models import GarmentORM


class InvoiceORM(Base):
    __tablename__ = "invoices"
    __table_args__ = (UniqueConstraint("invoice_number", name="uq_invoice_number"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    invoice_number: Mapped[str] = mapped_column(String(64), nullable=False)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    customer: Mapped["CustomerORM"] = relationship(back_populates="invoices")
    garments: Mapped[list["GarmentORM"]] = relationship(back_populates="invoice")
