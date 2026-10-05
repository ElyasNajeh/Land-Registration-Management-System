from fastapi import APIRouter, Depends, Query, status

from app.core.access import require_staff_access
from . import service
from .schemas import StaffCreate, StaffUpdate

router = APIRouter(prefix="/staff", tags=["Staff"], dependencies=[Depends(require_staff_access)])


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_staff(data: StaffCreate):
    return service.create_staff(data)


@router.get("/")
def list_staff(
    search: str | None = Query(default=None, max_length=100),
    role: str | None = None,
    active: bool | None = None,
    zone_id: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    return service.list_staff(search, role, active, zone_id, page, page_size)


@router.get("/{staff_id}")
def get_staff(staff_id: str):
    return service.get_staff(staff_id)


@router.patch("/{staff_id}")
def update_staff(staff_id: str, data: StaffUpdate):
    return service.update_staff(staff_id, data)
