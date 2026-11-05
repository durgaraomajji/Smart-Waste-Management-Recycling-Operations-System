from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.pagination import Page, PageParams
from app.core.permissions import MANAGEMENT, SUPERVISION
from app.core.responses import MessageResponse
from app.database.session import get_db
from app.dependencies import get_current_user, require_roles
from app.enums import ZoneStatus
from app.models import User
from app.schemas.collection_tracking import CollectionOut
from app.schemas.customer import (
    AddressCreate,
    AddressOut,
    AddressUpdate,
    CustomerCreate,
    CustomerOut,
    CustomerStatusUpdate,
    CustomerUpdate,
)
from app.services.customer_service import CustomerService

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.post("", response_model=CustomerOut, status_code=status.HTTP_201_CREATED, summary="Register a customer (staff)")
def create_customer(data: CustomerCreate, actor: User = Depends(require_roles(*SUPERVISION)), db: Session = Depends(get_db)):
    return CustomerService(db).create(actor, data)


@router.get("", response_model=Page[CustomerOut], summary="Customer search and filtering")
def list_customers(
    params: PageParams = Depends(),
    search: str | None = None,
    zone_id: int | None = None,
    service_status: ZoneStatus | None = None,
    _: User = Depends(require_roles(*SUPERVISION)),
    db: Session = Depends(get_db),
):
    return CustomerService(db).list(params, search=search, zone_id=zone_id, service_status=service_status)


@router.get("/me", response_model=CustomerOut, summary="My customer profile")
def my_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return CustomerService(db).for_user(user)


@router.get("/{customer_id}", response_model=CustomerOut)
def get_customer(customer_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return CustomerService(db).get(customer_id, user)


@router.patch("/{customer_id}", response_model=CustomerOut)
def update_customer(customer_id: int, data: CustomerUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return CustomerService(db).update(user, customer_id, data)


@router.patch("/{customer_id}/service-status", response_model=CustomerOut)
def set_service_status(customer_id: int, data: CustomerStatusUpdate, actor: User = Depends(require_roles(*MANAGEMENT)), db: Session = Depends(get_db)):
    return CustomerService(db).set_service_status(actor, customer_id, data.service_status)


@router.post("/{customer_id}/addresses", response_model=AddressOut, status_code=status.HTTP_201_CREATED, summary="Add an address with map coordinates")
def add_address(customer_id: int, data: AddressCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return CustomerService(db).add_address(user, customer_id, data)


@router.patch("/{customer_id}/addresses/{address_id}", response_model=AddressOut)
def update_address(customer_id: int, address_id: int, data: AddressUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return CustomerService(db).update_address(user, customer_id, address_id, data)


@router.delete("/{customer_id}/addresses/{address_id}", response_model=MessageResponse)
def delete_address(customer_id: int, address_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    CustomerService(db).delete_address(user, customer_id, address_id)
    return {"message": "Address deleted"}


@router.get("/{customer_id}/collections", response_model=Page[CollectionOut], summary="Collection history")
def collection_history(customer_id: int, params: PageParams = Depends(), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return CustomerService(db).collection_history(user, customer_id, params)
