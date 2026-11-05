from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.core.pagination import PageParams, paginate
from app.database.transaction import transaction
from app.enums import UserRole, ZoneStatus
from app.models import Customer, CustomerAddress, User
from app.repositories.collection_repository import CollectionRepository
from app.repositories.customer_repository import AddressRepository, CustomerRepository
from app.repositories.location_repository import ZoneRepository
from app.schemas.customer import AddressCreate, AddressUpdate, CustomerCreate, CustomerUpdate
from app.services.audit_service import AuditService
from app.utils.validators import get_or_404, validate_phone


class CustomerService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = CustomerRepository(db)
        self.addresses = AddressRepository(db)
        self.zones = ZoneRepository(db)
        self.audit = AuditService(db)

    # ------------------------------------------------------------ access control
    def get(self, customer_id: int, actor: User | None = None) -> Customer:
        customer = get_or_404(self.repo, customer_id, "Customer")
        if actor and actor.role == UserRole.CUSTOMER and customer.user_id != actor.id:
            raise ForbiddenError("You can only access your own customer profile")
        return customer

    def for_user(self, user: User) -> Customer:
        customer = self.repo.get_by_user(user.id)
        if not customer:
            raise NotFoundError("No customer profile is linked to this account")
        return customer

    # ------------------------------------------------------------------ create
    def create(self, actor: User, data: CustomerCreate) -> Customer:
        if data.email and self.repo.exists(email=data.email.lower()):
            raise ConflictError("A customer with this email already exists")
        validate_phone(data.phone)
        if data.zone_id:
            get_or_404(self.zones, data.zone_id, "Zone")
        with transaction(self.db):
            customer = self.repo.add(
                Customer(
                    customer_code=self.repo.next_number("CUS"),
                    full_name=data.full_name.strip(),
                    email=data.email.lower() if data.email else None,
                    phone=data.phone,
                    zone_id=data.zone_id,
                )
            )
            if data.address:
                self._add_address(customer, data.address)
            self.audit.log(actor, "CUSTOMER_CREATED", "customer", customer.id)
        self.db.refresh(customer)
        return customer

    def list(self, params: PageParams, **filters):
        return paginate(self.db, self.repo.filtered(**filters), params)

    def update(self, actor: User, customer_id: int, data: CustomerUpdate) -> Customer:
        customer = self.get(customer_id, actor)
        values = data.model_dump(exclude_unset=True)
        if "phone" in values:
            validate_phone(values["phone"])
        if values.get("zone_id"):
            get_or_404(self.zones, values["zone_id"], "Zone")
        with transaction(self.db):
            self.repo.update(customer, values)
            self.audit.log(actor, "CUSTOMER_UPDATED", "customer", customer.id, values)
        return customer

    def set_service_status(self, actor: User, customer_id: int, status: ZoneStatus) -> Customer:
        customer = self.get(customer_id)
        with transaction(self.db):
            old = customer.service_status
            customer.service_status = status
            self.audit.log(actor, "CUSTOMER_STATUS_CHANGED", "customer", customer.id, {"from": old.value, "to": status.value})
        return customer

    # --------------------------------------------------------------- addresses
    def _add_address(self, customer: Customer, data: AddressCreate) -> CustomerAddress:
        zone_id = data.zone_id or customer.zone_id
        if zone_id:
            get_or_404(self.zones, zone_id, "Zone")
        first = not self.addresses.for_customer(customer.id)
        make_default = data.is_default or first
        if make_default:
            self.addresses.clear_default(customer.id)
        payload = data.model_dump()
        payload.update(zone_id=zone_id, is_default=make_default)
        return self.addresses.add(CustomerAddress(customer_id=customer.id, **payload))

    def add_address(self, actor: User, customer_id: int, data: AddressCreate) -> CustomerAddress:
        customer = self.get(customer_id, actor)
        with transaction(self.db):
            addr = self._add_address(customer, data)
            self.audit.log(actor, "CUSTOMER_ADDRESS_ADDED", "customer", customer.id, {"address_id": addr.id})
        return addr

    def update_address(self, actor: User, customer_id: int, address_id: int, data: AddressUpdate) -> CustomerAddress:
        customer = self.get(customer_id, actor)
        addr = get_or_404(self.addresses, address_id, "Address")
        if addr.customer_id != customer.id:
            raise NotFoundError("Address not found")
        values = data.model_dump(exclude_unset=True)
        with transaction(self.db):
            if values.get("is_default"):
                self.addresses.clear_default(customer.id)
            self.addresses.update(addr, values)
            self.audit.log(actor, "CUSTOMER_ADDRESS_UPDATED", "customer", customer.id, {"address_id": addr.id})
        return addr

    def delete_address(self, actor: User, customer_id: int, address_id: int) -> None:
        customer = self.get(customer_id, actor)
        addr = get_or_404(self.addresses, address_id, "Address")
        if addr.customer_id != customer.id:
            raise NotFoundError("Address not found")
        with transaction(self.db):
            self.addresses.soft_delete(addr)
            self.audit.log(actor, "CUSTOMER_ADDRESS_DELETED", "customer", customer.id, {"address_id": address_id})

    # ----------------------------------------------------------------- history
    def collection_history(self, actor: User, customer_id: int, params: PageParams):
        customer = self.get(customer_id, actor)
        return paginate(self.db, CollectionRepository(self.db).filtered(customer_id=customer.id), params)
