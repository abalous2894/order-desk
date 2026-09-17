from pydantic import BaseModel, Field


class CustomerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    phone: str = Field(min_length=1, max_length=32)


class CustomerRead(BaseModel):
    id: int
    name: str
    phone: str

    model_config = {"from_attributes": True}


class CustomerProfile(CustomerRead):
    invoice_count: int
    garment_count: int
