from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, EmailStr, Field


NonEmpty = Annotated[str, Field(min_length=1, max_length=500)]


class ApplicantType(str, Enum):
    CITIZEN = "citizen"
    LAWYER = "lawyer"
    COMPANY = "company"
    SURVEYOR = "surveyor"
    AUTHORIZED_REPRESENTATIVE = "authorized_representative"


class Contacts(BaseModel):
    email: EmailStr
    phone: NonEmpty


class Address(BaseModel):
    city: NonEmpty
    street: str | None = Field(default=None, max_length=300)
    neighborhood: str | None = Field(default=None, max_length=300)
    zone_id: str | None = Field(default=None, max_length=100)


class NotificationPreferences(BaseModel):
    on_status_change: bool = True
    on_missing_documents: bool = True
    on_certificate_ready: bool = True


class Preferences(BaseModel):
    preferred_contact: Literal["email", "phone"] = "email"
    language: Literal["ar", "en"] = "ar"
    notifications: NotificationPreferences = Field(default_factory=NotificationPreferences)


class ApplicantCreate(BaseModel):
    full_name: NonEmpty
    applicant_type: ApplicantType
    national_id: Annotated[str, Field(min_length=4, max_length=50)]
    contacts: Contacts
    address: Address
    preferences: Preferences = Field(default_factory=Preferences)


class ApplicantUpdate(BaseModel):
    full_name: NonEmpty | None = None
    contacts: Contacts | None = None
    address: Address | None = None
    preferences: Preferences | None = None
    verification_state: Literal["unverified", "verified", "suspended"] | None = None


class ApplicationDocumentCreate(BaseModel):
    document_type: NonEmpty
    file_name: NonEmpty
    file_url: str | None = None
    mime_type: str | None = None
    file_size: int | None = Field(default=None, ge=0)
    uploaded_by_applicant_id: str | None = None
    notes: str | None = Field(default=None, max_length=1000)


class ApplicationCommentCreate(BaseModel):
    comment: Annotated[str, Field(min_length=1, max_length=2000)]


class ApplicationObjectionCreate(BaseModel):
    reason: Annotated[str, Field(min_length=1, max_length=2000)]
    submitted_by_applicant_id: str | None = None
