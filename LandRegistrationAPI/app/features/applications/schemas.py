from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, field_validator

from .enums import ApplicationStatus, ApplicationType


NonEmpty = Annotated[str, Field(min_length=1, max_length=500)]


class Geometry(BaseModel):
    type: Literal["Point", "Polygon"]
    coordinates: list[Any]

    @field_validator("coordinates")
    @classmethod
    def coordinates_are_present(cls, value):
        if not value:
            raise ValueError("Geometry coordinates are required")
        return value


class DocumentInput(BaseModel):
    document_type: NonEmpty
    file_name: NonEmpty | None = None
    file_url: str | None = None
    mime_type: str | None = None
    file_size: int | None = Field(default=None, ge=0)
    notes: str | None = Field(default=None, max_length=1000)


class CreateApplicationRequest(BaseModel):
    application_type: ApplicationType
    applicant_id: NonEmpty
    parcel_id: NonEmpty
    parcel_number: NonEmpty
    block_number: NonEmpty
    basin_number: NonEmpty
    zone_id: NonEmpty
    geometry: Geometry | None = None
    description: str | None = Field(default=None, max_length=2000)
    priority: Literal["low", "normal", "high", "urgent"] = "normal"
    documents: list[DocumentInput] = Field(default_factory=list, max_length=20)


class UpdateApplicationRequest(BaseModel):
    description: str | None = Field(default=None, max_length=2000)
    priority: Literal["low", "normal", "high", "urgent"] | None = None
    tags: list[str] | None = Field(default=None, max_length=20)


class TransitionRequest(BaseModel):
    new_status: ApplicationStatus


class ReasonRequest(BaseModel):
    reason: NonEmpty


class NoteRequest(BaseModel):
    note: NonEmpty
    visibility: Literal["staff_only", "applicant_visible"] = "staff_only"


class MissingDocumentsRequest(BaseModel):
    documents: list[NonEmpty] = Field(min_length=1, max_length=20)


class DocumentReviewRequest(BaseModel):
    status: Literal["verified", "rejected", "pending_review"]
    notes: str | None = Field(default=None, max_length=1000)
