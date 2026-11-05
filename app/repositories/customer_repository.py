from sqlalchemy import or_

from app.enums import ZoneStatus
from app.models import Customer, CustomerAddress
from app.repositories.base_repository import BaseRepository


class CustomerRepository(BaseRepository[Customer]):
    model = Customer

    def get_by_user(self, user_id: int) -> Customer | None:
        return self.get_by(user_id=user_id)

    def filtered(self, search: str | None = None, zone_id: int | None = None, service_status: ZoneStatus | None = None):
        stmt = self.select()
        if search:
            like = f"%{search}%"
            stmt = stmt.where(
                or_(Customer.full_name.ilike(like), Customer.email.ilike(like), Customer.phone.ilike(like), Customer.customer_code.ilike(like))
            )
        if zone_id:
            stmt = stmt.where(Customer.zone_id == zone_id)
        if service_status:
            stmt = stmt.where(Customer.service_status == service_status)
        return stmt.order_by(Customer.id.desc())


class AddressRepository(BaseRepository[CustomerAddress]):
    model = CustomerAddress

    def for_customer(self, customer_id: int) -> list[CustomerAddress]:
        return list(self.db.scalars(self.select().where(CustomerAddress.customer_id == customer_id)).all())

    def clear_default(self, customer_id: int) -> None:
        for a in self.for_customer(customer_id):
            a.is_default = False
        self.db.flush()
