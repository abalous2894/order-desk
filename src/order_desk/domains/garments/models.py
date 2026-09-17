from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from order_desk.db.base import Base

if TYPE_CHECKING:
    from order_desk.domains.customers.models import CustomerORM
    from order_desk.domains.invoices.models import InvoiceORM


class GarmentORM(Base):
    __tablename__ = "garments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    garment_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="received")

    customer: Mapped["CustomerORM"] = relationship(back_populates="garments")
    invoice: Mapped["InvoiceORM"] = relationship(back_populates="garments")
