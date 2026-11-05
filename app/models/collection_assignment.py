from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.enums import AssignmentStatus
from app.models.base_model import BaseModel, EnumType

assignment_workers = Table(
    "assignment_workers",
    Base.metadata,
    Column("assignment_id", ForeignKey("collection_assignments.id"), primary_key=True),
    Column("worker_id", ForeignKey("field_workers.id"), primary_key=True),
)


class CollectionAssignment(Base, BaseModel):
    __tablename__ = "collection_assignments"

    pickup_request_id: Mapped[int] = mapped_column(ForeignKey("pickup_requests.id"), index=True, nullable=False)
    driver_id: Mapped[int] = mapped_column(ForeignKey("drivers.id"), index=True, nullable=False)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id"), index=True, nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime, index=True, nullable=False)
    status: Mapped[AssignmentStatus] = mapped_column(EnumType(AssignmentStatus), default=AssignmentStatus.ASSIGNED, nullable=False, index=True)
    assigned_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)

    workers = relationship("FieldWorker", secondary=assignment_workers, lazy="selectin")
