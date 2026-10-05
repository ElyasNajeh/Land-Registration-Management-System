from fastapi import APIRouter, Depends, Query

from app.core.access import require_staff_access
from . import service
from .schemas import RegistrarReviewRequest, SurveyMilestoneRequest, SurveyReportRequest

router = APIRouter(tags=["Assignments"], dependencies=[Depends(require_staff_access)])


@router.get("/survey-tasks/")
def list_tasks(
    surveyor_id: str | None = None,
    status: str | None = None,
    zone_id: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    return service.list_tasks(surveyor_id, status, zone_id, page, page_size)


@router.post("/applications/{application_id}/auto-assign-surveyor")
def auto_assign_surveyor(application_id: str):
    return service.auto_assign_surveyor(application_id)


@router.patch("/applications/{application_id}/survey-milestone")
def add_survey_milestone(application_id: str, data: SurveyMilestoneRequest):
    return service.add_milestone(application_id, data)


@router.post("/applications/{application_id}/survey-report")
def add_survey_report(application_id: str, data: SurveyReportRequest):
    return service.add_report(application_id, data)


@router.patch("/applications/{application_id}/registrar-review")
def registrar_review(application_id: str, data: RegistrarReviewRequest):
    return service.registrar_review(application_id, data)
