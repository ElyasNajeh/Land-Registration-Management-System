from fastapi import APIRouter, Depends, Query, status

from app.core.access import require_staff_access
from . import service
from .schemas import (
    ApplicantCreate,
    ApplicantUpdate,
    ApplicationCommentCreate,
    ApplicationDocumentCreate,
    ApplicationObjectionCreate,
)

router = APIRouter(tags=["Applicants"])


@router.post("/applicants/", status_code=status.HTTP_201_CREATED)
def create_applicant(data: ApplicantCreate):
    return service.create_applicant(data)


@router.get("/applicants/", dependencies=[Depends(require_staff_access)])
def list_applicants(
    search: str | None = Query(default=None, max_length=100),
    applicant_type: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    return service.list_applicants(search, applicant_type, page, page_size)


@router.get("/applicants/{applicant_id}")
def get_applicant(applicant_id: str):
    return service.get_applicant(applicant_id)


@router.patch("/applicants/{applicant_id}", dependencies=[Depends(require_staff_access)])
def update_applicant(applicant_id: str, data: ApplicantUpdate):
    return service.update_applicant(applicant_id, data)


@router.get("/applicants/{applicant_id}/applications")
def list_applicant_applications(
    applicant_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    return service.list_applicant_applications(applicant_id, page, page_size)


@router.post("/applications/{application_id}/documents", status_code=status.HTTP_201_CREATED)
def add_document(application_id: str, data: ApplicationDocumentCreate):
    return service.add_document(application_id, data)


@router.post("/applications/{application_id}/comments", status_code=status.HTTP_201_CREATED)
def add_comment(application_id: str, data: ApplicationCommentCreate):
    return service.add_comment(application_id, data)


@router.post("/applications/{application_id}/objections", status_code=status.HTTP_201_CREATED)
def submit_objection(application_id: str, data: ApplicationObjectionCreate):
    return service.submit_objection(application_id, data)


@router.get("/applications/{application_id}/timeline")
def get_timeline(application_id: str):
    return service.get_timeline(application_id)
