from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from order_desk.domains.customers.models import CustomerORM
from order_desk.domains.garments.models import GarmentORM
from order_desk.domains.invoices.models import InvoiceORM
from order_desk.util.text import escape_like, normalize_phone


class CustomerRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, name: str, phone: str) -> CustomerORM:
        customer = CustomerORM(name=name.strip(), phone=normalize_phone(phone))
        self.db.add(customer)
        self.db.flush()
        return customer

    def get_by_id(self, customer_id: int) -> CustomerORM | None:
        return self.db.get(CustomerORM, customer_id)

    def find_by_phone(self, phone: str) -> CustomerORM | None:
        normalized = normalize_phone(phone)
        stmt = select(CustomerORM).where(CustomerORM.phone == normalized)
        return self.db.scalar(stmt)

    def search(self, query: str, limit: int = 20) -> list[CustomerORM]:
        q = query.strip()
        if not q:
            return []
        phone_q = normalize_phone(q) if q.replace("-", "").isdigit() else q
        name_pattern = f"%{escape_like(q)}%"
        phone_pattern = f"%{escape_like(phone_q)}%"
        stmt = (
            select(CustomerORM)
            .where(
                or_(
                    CustomerORM.phone.ilike(phone_pattern, escape="\\"),
                    CustomerORM.name.ilike(name_pattern, escape="\\"),
                )
            )
            .order_by(CustomerORM.name)
            .limit(limit)
        )
        return list(self.db.scalars(stmt))

    def profile_counts(self, customer_id: int) -> tuple[int, int]:
        inv = self.db.scalar(
            select(func.count()).select_from(InvoiceORM).where(InvoiceORM.customer_id == customer_id)
        )
        gar = self.db.scalar(
            select(func.count()).select_from(GarmentORM).where(GarmentORM.customer_id == customer_id)
        )
        return int(inv or 0), int(gar or 0)
