from sqlalchemy import or_

from app.enums import ZoneStatus
from app.models import CollectionArea, CollectionSchedule, ServiceZone, Street
from app.repositories.base_repository import BaseRepository


class ZoneRepository(BaseRepository[ServiceZone]):
    model = ServiceZone

    def filtered(self, search: str | None = None, status: ZoneStatus | None = None, supervisor_id: int | None = None):
        stmt = self.select()
        if search:
            like = f"%{search}%"
            stmt = stmt.where(or_(ServiceZone.name.ilike(like), ServiceZone.code.ilike(like)))
        if status:
            stmt = stmt.where(ServiceZone.status == status)
        if supervisor_id:
            stmt = stmt.where(ServiceZone.supervisor_id == supervisor_id)
        return stmt.order_by(ServiceZone.name)


class AreaRepository(BaseRepository[CollectionArea]):
    model = CollectionArea

    def filtered(self, zone_id: int | None = None, search: str | None = None):
        stmt = self.select()
        if zone_id:
            stmt = stmt.where(CollectionArea.zone_id == zone_id)
        if search:
            stmt = stmt.where(CollectionArea.name.ilike(f"%{search}%"))
        return stmt.order_by(CollectionArea.name)


class StreetRepository(BaseRepository[Street]):
    model = Street

    def filtered(self, area_id: int | None = None, locality: str | None = None, search: str | None = None):
        stmt = self.select()
        if area_id:
            stmt = stmt.where(Street.area_id == area_id)
        if locality:
            stmt = stmt.where(Street.locality.ilike(f"%{locality}%"))
        if search:
            stmt = stmt.where(Street.name.ilike(f"%{search}%"))
        return stmt.order_by(Street.name)


class ScheduleRepository(BaseRepository[CollectionSchedule]):
    model = CollectionSchedule

    def filtered(self, zone_id: int | None = None, day_of_week: int | None = None):
        stmt = self.select()
        if zone_id:
            stmt = stmt.where(CollectionSchedule.zone_id == zone_id)
        if day_of_week is not None:
            stmt = stmt.where(CollectionSchedule.day_of_week == day_of_week)
        return stmt.order_by(CollectionSchedule.day_of_week, CollectionSchedule.start_time)
