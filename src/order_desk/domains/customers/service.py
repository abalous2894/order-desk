from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from order_desk.domains.customers.repository import CustomerRepository
from order_desk.domains.customers.schemas import CustomerCreate, CustomerProfile, CustomerRead
from order_desk.util.text import (
    InvalidCustomerNameError,
    InvalidPhoneError,
    validate_customer_name,
    validate_phone,
)


class CustomerServiceError(ValueError):
    pass


class CustomerService:
    def __init__(self, db: Session) -> None:
        self.repo = CustomerRepository(db)
        self.db = db

    def _validated_name(self, name: str) -> str:
        try:
            return validate_customer_name(name)
        except InvalidCustomerNameError as exc:
            raise CustomerServiceError(str(exc)) from exc

    def _validated_phone(self, phone: str) -> str:
        try:
            return validate_phone(phone)
        except InvalidPhoneError as exc:
            raise CustomerServiceError(str(exc)) from exc

    def _create_row(self, name: str, phone: str) -> CustomerRead:
        if self.repo.find_by_phone(phone):
            raise CustomerServiceError("Customer with this phone already exists")
        try:
            row = self.repo.create(name, phone)
            self.db.commit()
            self.db.refresh(row)
            return CustomerRead.model_validate(row)
        except IntegrityError as exc:
            self.db.rollback()
            raise CustomerServiceError("Customer name and phone combination already exists") from exc

    def create(self, payload: CustomerCreate) -> CustomerRead:
        name = self._validated_name(payload.name)
        phone = self._validated_phone(payload.phone)
        return self._create_row(name, phone)

    def get_or_create(self, payload: CustomerCreate) -> CustomerRead:
        name = self._validated_name(payload.name)
        phone = self._validated_phone(payload.phone)
        existing = self.repo.find_by_phone(phone)
        if existing:
            if existing.name.strip().lower() != name.lower():
                raise CustomerServiceError(
                    "Phone exists under a different customer name; verify the profile first"
                )
            return CustomerRead.model_validate(existing)
        return self._create_row(name, phone)

    def get(self, customer_id: int) -> CustomerRead:
        row = self.repo.get_by_id(customer_id)
        if not row:
            raise CustomerServiceError("Customer not found")
        return CustomerRead.model_validate(row)

    def search(self, query: str) -> list[CustomerRead]:
        rows = self.repo.search(query)
        return [CustomerRead.model_validate(r) for r in rows]

    def profile(self, customer_id: int) -> CustomerProfile:
        row = self.repo.get_by_id(customer_id)
        if not row:
            raise CustomerServiceError("Customer not found")
        inv_count, gar_count = self.repo.profile_counts(customer_id)
        return CustomerProfile(
            id=row.id,
            name=row.name,
            phone=row.phone,
            invoice_count=inv_count,
            garment_count=gar_count,
        )
