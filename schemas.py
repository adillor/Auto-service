from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ClientCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    phone: str = Field(min_length=1, max_length=50)


class ClientUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    phone: str | None = Field(default=None, min_length=1, max_length=50)


class ClientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    phone: str


class CarCreate(BaseModel):
    owner_id: int = Field(gt=0)
    make: str = Field(min_length=1, max_length=100)
    model: str = Field(min_length=1, max_length=100)
    vin: str = Field(min_length=1, max_length=100)


class CarResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    make: str
    model: str
    vin: str
    owner_id: int | None


class ServiceCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    price: Decimal = Field(gt=0)


class ServiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    price: Decimal


class OrderCreate(BaseModel):
    car_id: int = Field(gt=0)
    mechanic_id: int | None = Field(default=None, gt=0)
    service_ids: list[int] = Field(min_length=1)


class OrderStatusUpdate(BaseModel):
    status: str = Field(pattern="^(in_progress|completed)$")


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    car_id: int
    mechanic_id: int | None
    status: str
    created_at: datetime
