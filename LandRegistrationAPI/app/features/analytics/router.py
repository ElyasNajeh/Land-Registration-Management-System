from fastapi import APIRouter, Depends, Query

from app.core.access import require_staff_access
from . import service

router = APIRouter(prefix="/analytics", tags=["Analytics"], dependencies=[Depends(require_staff_access)])


@router.get("/kpis")
def kpis():
    return service.kpis()


@router.get("/applications-by-status")
def applications_by_status():
    return service.grouped("status")


@router.get("/applications-by-type")
def applications_by_type():
    return service.grouped("application_type")


@router.get("/applications-by-zone")
def applications_by_zone():
    return service.grouped("parcel_ref.zone_id")


@router.get("/processing-time")
def processing_time():
    return service.processing_time()


@router.get("/surveyors")
def surveyors():
    return service.surveyors()


@router.get("/registrars")
def registrars():
    return service.registrars()


@router.get("/geofeeds/parcels")
def parcel_feed(
    zone_id: str | None = None,
    status: str | None = None,
    application_type: str | None = None,
    limit: int = Query(default=500, ge=1, le=2000),
):
    return service.parcel_feed(zone_id, status, application_type, limit)


@router.get("/geofeeds/pending-heatmap")
def pending_heatmap(zone_id: str | None = None, limit: int = Query(default=500, ge=1, le=2000)):
    return service.pending_heatmap(zone_id, limit)
