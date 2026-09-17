from datetime import datetime

from pydantic import BaseModel, Field


class InvoiceCreate(BaseModel):
    customer_id: int = Field(gt=0)
    invoice_number: str = Field(min_length=1, max_length=64)


class InvoiceRead(BaseModel):
    id: int
    invoice_number: str
    customer_id: int
    created_at: datetime

    model_config = {"from_attributes": True}
