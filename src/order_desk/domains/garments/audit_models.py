from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from order_desk.db.base import Base


class GarmentStatusEventORM(Base):
    """Append-only audit log for garment status changes."""

    __tablename__ = "garment_status_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    garment_id: Mapped[int] = mapped_column(
        ForeignKey("garments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    from_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    to_status: Mapped[str] = mapped_column(String(32), nullable=False)
    actor: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
