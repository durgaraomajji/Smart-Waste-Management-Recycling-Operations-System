from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.enums import ZoneStatus
from app.schemas.common import ORMModel


class AddressCreate(BaseModel):
    label: str = Field(default="home", max_length=50)
    line1: str = Field(min_length=3, max_length=255)
    line2: str | None = None
    street_id: int | None = None
    area_id: int | None = None
    zone_id: int | None = None
    city: str = Field(min_length=2, max_length=100)
    pincode: str | None = Field(default=None, max_length=10)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    is_default: bool = False


class AddressUpdate(BaseModel):
    label: str | None = None
    line1: str | None = None
    line2: str | None = None
    city: str | None = None
    pincode: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    is_default: bool | None = None


class AddressOut(ORMModel):
    id: int
    customer_id: int
    label: str
    line1: str
    line2: str | None
    street_id: int | None
    area_id: int | None
    zone_id: int | None
    city: str
    pincode: str | None
    latitude: float | None
    longitude: float | None
    is_default: bool


class CustomerCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=20)
    zone_id: int | None = None
    address: AddressCreate | None = None


class CustomerUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    phone: str | None = None
    zone_id: int | None = None


class CustomerStatusUpdate(BaseModel):
    service_status: ZoneStatus


class CustomerOut(ORMModel):
    id: int
    user_id: int | None
    customer_code: str
    full_name: str
    email: str | None
    phone: str | None
    zone_id: int | None
    service_status: ZoneStatus
    created_at: datetime
    addresses: list[AddressOut] = []
