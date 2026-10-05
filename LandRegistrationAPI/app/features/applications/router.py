from datetime import date, datetime, time, timezone
from typing import Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status

from app.core.access import require_staff_access
from .schemas import (
    CreateApplicationRequest,
    DocumentReviewRequest,
    MissingDocumentsRequest,
    NoteRequest,
    ReasonRequest,
    TransitionRequest,
    UpdateApplicationRequest,
)
from .services import application_service as service

router = APIRouter(prefix="/applications", tags=["Applications"])


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_application(
    data: CreateApplicationRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key", max_length=100),
):
    return service.create_application(data, idempotency_key)


@router.get("/")
def list_applications(
    search: str | None = Query(default=None, max_length=100),
    status_filter: str | None = Query(default=None, alias="status"),
    application_type: str | None = None,
    priority: str | None = None,
    zone_id: str | None = None,
    applicant_id: str | None = None,
    parcel_number: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort_field: Literal[
        "timestamps.submitted_at", "timestamps.updated_at", "application_id", "status", "priority"
    ] = "timestamps.submitted_at",
    sort_order: int = Query(default=-1),
):
    if sort_order not in (-1, 1):
        raise HTTPException(status_code=422, detail="sort_order must be -1 or 1")
    filters = {
        "search": search,
        "status": status_filter,
        "application_type": application_type,
        "priority": priority,
        "zone_id": zone_id,
        "applicant_id": applicant_id,
        "parcel_number": parcel_number,
        "date_from": datetime.combine(date_from, time.min, tzinfo=timezone.utc) if date_from else None,
        "date_to": datetime.combine(date_to, time.max, tzinfo=timezone.utc) if date_to else None,
    }
    return service.list_applications(filters, page, page_size, sort_field, sort_order)


@router.get("/{application_id}")
def get_application(application_id: str):
    return service.get_application(application_id)


@router.patch("/{application_id}", dependencies=[Depends(require_staff_access)])
def update_application(application_id: str, data: UpdateApplicationRequest):
    return service.update_application(application_id, data)


@router.delete("/{application_id}", dependencies=[Depends(require_staff_access)])
def delete_application(application_id: str):
    return service.delete_application(application_id)


@router.patch("/{application_id}/transition", dependencies=[Depends(require_staff_access)])
def transition_application(application_id: str, data: TransitionRequest):
    return service.transition_application(application_id, data.new_status)


@router.post("/{application_id}/hold", dependencies=[Depends(require_staff_access)])
def hold_application(application_id: str, data: ReasonRequest):
    return service.interrupt_application(application_id, "on_hold", data.reason, "hold_reason")


@router.post("/{application_id}/reject", dependencies=[Depends(require_staff_access)])
def reject_application(application_id: str, data: ReasonRequest):
    return service.reject_application(application_id, data.reason)


@router.post("/{application_id}/certificate", dependencies=[Depends(require_staff_access)])
def generate_certificate(application_id: str):
    return service.generate_certificate(application_id)


@router.post("/{application_id}/notes", dependencies=[Depends(require_staff_access)])
def add_note(application_id: str, data: NoteRequest):
    return service.add_note(application_id, data.note, data.visibility)


@router.post("/{application_id}/missing-documents", dependencies=[Depends(require_staff_access)])
def missing_documents(application_id: str, data: MissingDocumentsRequest):
    return service.mark_missing_documents(application_id, data.documents)


@router.post("/{application_id}/objection")
def objection(application_id: str, data: ReasonRequest):
    return service.interrupt_application(application_id, "under_objection", data.reason, "objection_reason")


@router.patch("/{application_id}/documents/{document_id}", dependencies=[Depends(require_staff_access)])
def review_document(application_id: str, document_id: str, data: DocumentReviewRequest):
    return service.review_document(application_id, document_id, data)
