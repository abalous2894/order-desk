from datetime import datetime

from pydantic import BaseModel, Field


class GarmentCreate(BaseModel):
    customer_id: int = Field(gt=0)
    invoice_number: str = Field(min_length=1, max_length=64)
    garment_type: str = Field(min_length=1, max_length=64)
    status: str = "received"


class GarmentStatusUpdate(BaseModel):
    status: str


class GarmentRead(BaseModel):
    id: int
    customer_id: int
    invoice_id: int
    invoice_number: str
    garment_type: str
    status: str

    model_config = {"from_attributes": True}


class GarmentStatusEventRead(BaseModel):
    id: int
    garment_id: int
    from_status: str | None
    to_status: str
    actor: str
    created_at: datetime

    model_config = {"from_attributes": True}
