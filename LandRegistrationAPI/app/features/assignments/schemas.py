from enum import Enum
from typing import Any, Annotated

from pydantic import BaseModel, Field


NonEmpty = Annotated[str, Field(min_length=1, max_length=1000)]


class SurveyMilestoneType(str, Enum):
    VISIT_SCHEDULED = "visit_scheduled"
    ARRIVED_ON_SITE = "arrived_on_site"
    SURVEY_STARTED = "survey_started"
    SURVEY_COMPLETED = "survey_completed"


class MilestoneActor(str, Enum):
    SYSTEM = "system"
    SURVEYOR = "surveyor"
    REGISTRAR = "registrar"


class SurveyMilestoneRequest(BaseModel):
    milestone_type: SurveyMilestoneType
    by: MilestoneActor
    meta: dict[str, Any] = Field(default_factory=dict)


class SurveyReportRequest(BaseModel):
    uploaded_by: NonEmpty
    report_title: NonEmpty
    summary: NonEmpty
    file_name: NonEmpty
    file_url: str | None = None


class RegistrarDecision(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_CORRECTION = "needs_correction"


class RegistrarReviewRequest(BaseModel):
    reviewed_by: NonEmpty
    decision: RegistrarDecision
    notes: NonEmpty
