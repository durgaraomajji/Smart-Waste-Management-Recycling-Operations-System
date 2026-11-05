from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError
from app.core.pagination import PageParams, paginate
from app.database.transaction import transaction
from app.enums import UserRole, ZoneStatus
from app.models import CollectionArea, CollectionSchedule, ServiceZone, Street, User
from app.repositories.location_repository import AreaRepository, ScheduleRepository, StreetRepository, ZoneRepository
from app.repositories.user_repository import UserRepository
from app.schemas.location import AreaCreate, ScheduleCreate, StreetCreate, ZoneCreate, ZoneUpdate
from app.services.audit_service import AuditService
from app.utils.validators import get_or_404, require_user_with_role

SUPERVISOR_ROLES = (UserRole.COLLECTION_SUPERVISOR, UserRole.OPERATIONS_MANAGER, UserRole.SUPER_ADMIN)


class LocationService:
    def __init__(self, db: Session):
        self.db = db
        self.zones = ZoneRepository(db)
        self.areas = AreaRepository(db)
        self.streets = StreetRepository(db)
        self.schedules = ScheduleRepository(db)
        self.users = UserRepository(db)
        self.audit = AuditService(db)

    # ------------------------------------------------------------------- zones
    def create_zone(self, actor: User, data: ZoneCreate) -> ServiceZone:
        if self.zones.exists(name=data.name) or self.zones.exists(code=data.code.upper()):
            raise ConflictError("A zone with this name or code already exists")
        if data.supervisor_id:
            require_user_with_role(self.users, data.supervisor_id, SUPERVISOR_ROLES, "Supervisor")
        with transaction(self.db):
            zone = self.zones.add(
                ServiceZone(name=data.name, code=data.code.upper(), description=data.description, supervisor_id=data.supervisor_id)
            )
            self.audit.log(actor, "ZONE_CREATED", "service_zone", zone.id, {"code": zone.code})
        return zone

    def get_zone(self, zone_id: int) -> ServiceZone:
        return get_or_404(self.zones, zone_id, "Zone")

    def list_zones(self, params: PageParams, **filters):
        return paginate(self.db, self.zones.filtered(**filters), params)

    def update_zone(self, actor: User, zone_id: int, data: ZoneUpdate) -> ServiceZone:
        zone = self.get_zone(zone_id)
        values = data.model_dump(exclude_unset=True)
        if "name" in values and values["name"] != zone.name and self.zones.exists(name=values["name"]):
            raise ConflictError("A zone with this name already exists")
        with transaction(self.db):
            self.zones.update(zone, values)
            self.audit.log(actor, "ZONE_UPDATED", "service_zone", zone.id, values)
        return zone

    def set_zone_status(self, actor: User, zone_id: int, status: ZoneStatus) -> ServiceZone:
        zone = self.get_zone(zone_id)
        with transaction(self.db):
            old = zone.status
            zone.status = status
            self.audit.log(actor, "ZONE_STATUS_CHANGED", "service_zone", zone.id, {"from": old.value, "to": status.value})
        return zone

    def assign_supervisor(self, actor: User, zone_id: int, supervisor_id: int) -> ServiceZone:
        zone = self.get_zone(zone_id)
        require_user_with_role(self.users, supervisor_id, SUPERVISOR_ROLES, "Supervisor")
        with transaction(self.db):
            zone.supervisor_id = supervisor_id
            self.audit.log(actor, "ZONE_SUPERVISOR_ASSIGNED", "service_zone", zone.id, {"supervisor_id": supervisor_id})
        return zone

    def delete_zone(self, actor: User, zone_id: int) -> None:
        zone = self.get_zone(zone_id)
        with transaction(self.db):
            self.zones.soft_delete(zone)
            self.audit.log(actor, "ZONE_DELETED", "service_zone", zone.id)

    # ------------------------------------------------------------------- areas
    def create_area(self, actor: User, data: AreaCreate) -> CollectionArea:
        self.get_zone(data.zone_id)
        if self.areas.get_by(zone_id=data.zone_id, name=data.name):
            raise ConflictError("This zone already has an area with that name")
        if data.supervisor_id:
            require_user_with_role(self.users, data.supervisor_id, SUPERVISOR_ROLES, "Supervisor")
        with transaction(self.db):
            area = self.areas.add(CollectionArea(zone_id=data.zone_id, name=data.name, supervisor_id=data.supervisor_id))
            self.audit.log(actor, "AREA_CREATED", "collection_area", area.id, {"zone_id": data.zone_id})
        return area

    def get_area(self, area_id: int) -> CollectionArea:
        return get_or_404(self.areas, area_id, "Area")

    def list_areas(self, params: PageParams, **filters):
        return paginate(self.db, self.areas.filtered(**filters), params)

    # ----------------------------------------------------------------- streets
    def add_street(self, actor: User, area_id: int, data: StreetCreate) -> Street:
        self.get_area(area_id)
        if self.streets.get_by(area_id=area_id, name=data.name, locality=data.locality):
            raise ConflictError("Street already exists in this area")
        with transaction(self.db):
            street = self.streets.add(Street(area_id=area_id, **data.model_dump()))
            self.audit.log(actor, "STREET_ADDED", "street", street.id, {"area_id": area_id})
        return street

    def list_streets(self, params: PageParams, **filters):
        return paginate(self.db, self.streets.filtered(**filters), params)

    # --------------------------------------------------------------- schedules
    def create_schedule(self, actor: User, data: ScheduleCreate) -> CollectionSchedule:
        self.get_zone(data.zone_id)
        if data.area_id:
            area = self.get_area(data.area_id)
            if area.zone_id != data.zone_id:
                raise ConflictError("Area does not belong to the given zone")
        with transaction(self.db):
            sched = self.schedules.add(CollectionSchedule(**data.model_dump()))
            self.audit.log(actor, "SCHEDULE_CREATED", "collection_schedule", sched.id, {"zone_id": data.zone_id})
        return sched

    def list_schedules(self, params: PageParams, **filters):
        return paginate(self.db, self.schedules.filtered(**filters), params)

    def deactivate_schedule(self, actor: User, schedule_id: int) -> CollectionSchedule:
        sched = get_or_404(self.schedules, schedule_id, "Schedule")
        with transaction(self.db):
            sched.is_active = False
            self.audit.log(actor, "SCHEDULE_DEACTIVATED", "collection_schedule", sched.id)
        return sched
