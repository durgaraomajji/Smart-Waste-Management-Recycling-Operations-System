from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.enums import WorkforceStatus
from app.schemas.common import ORMModel


class DriverCreate(BaseModel):
    user_id: int | None = None
    employee_code: str = Field(min_length=2, max_length=30)
    full_name: str = Field(min_length=2, max_length=150)
    phone: str = Field(min_length=7, max_length=20)
    email: EmailStr | None = None
    license_number: str = Field(min_length=4, max_length=40)
    license_expiry: date
    license_class: str | None = None
    skills: list[str] = []
    supervisor_id: int | None = None

    @field_validator("license_expiry")
    @classmethod
    def _valid_license(cls, v: date):
        if v <= date.today():
            raise ValueError("Driving licence is expired")
        return v


class WorkerCreate(BaseModel):
    user_id: int | None = None
    employee_code: str = Field(min_length=2, max_length=30)
    full_name: str = Field(min_length=2, max_length=150)
    phone: str = Field(min_length=7, max_length=20)
    email: EmailStr | None = None
    skills: list[str] = []
    supervisor_id: int | None = None


class WorkforceUpdate(BaseModel):
    phone: str | None = None
    skills: list[str] | None = None
    supervisor_id: int | None = None


class WorkforceStatusUpdate(BaseModel):
    status: WorkforceStatus


class DriverOut(ORMModel):
    id: int
    user_id: int | None
    employee_code: str
    full_name: str
    phone: str
    email: str | None
    license_number: str
    license_expiry: date
    license_class: str | None
    skills: list[str] | None
    status: WorkforceStatus
    supervisor_id: int | None


class WorkerOut(ORMModel):
    id: int
    user_id: int | None
    employee_code: str
    full_name: str
    phone: str
    email: str | None
    skills: list[str] | None
    status: WorkforceStatus
    supervisor_id: int | None


class WorkforceHistoryItem(ORMModel):
    assignment_id: int
    pickup_request_id: int
    vehicle_id: int
    scheduled_at: datetime
    status: str
