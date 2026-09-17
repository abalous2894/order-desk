from typing import TYPE_CHECKING

from sqlalchemy import Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from order_desk.db.base import Base

if TYPE_CHECKING:
    from order_desk.domains.garments.models import GarmentORM
    from order_desk.domains.invoices.models import InvoiceORM


class CustomerORM(Base):
    __tablename__ = "customers"
    __table_args__ = (
        UniqueConstraint("name", "phone", name="uq_customer_name_phone"),
        Index("ix_customers_phone", "phone"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)

    invoices: Mapped[list["InvoiceORM"]] = relationship(back_populates="customer")
    garments: Mapped[list["GarmentORM"]] = relationship(back_populates="customer")
