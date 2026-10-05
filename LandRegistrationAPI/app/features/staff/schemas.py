from enum import Enum
from typing import Annotated

from pydantic import BaseModel, EmailStr, Field, model_validator


NonEmpty = Annotated[str, Field(min_length=1, max_length=500)]


class StaffRole(str, Enum):
    SURVEYOR = "surveyor"
    REGISTRAR = "registrar"
    OFFICER = "officer"


class ContactInfo(BaseModel):
    phone: NonEmpty
    email: EmailStr


class Coverage(BaseModel):
    zone_ids: list[NonEmpty] = Field(default_factory=list, max_length=100)


class Workload(BaseModel):
    active_tasks: int = Field(default=0, ge=0)
    max_tasks: int = Field(default=10, ge=1, le=1000)

    @model_validator(mode="after")
    def validate_capacity(self):
        if self.active_tasks > self.max_tasks:
            raise ValueError("active_tasks cannot exceed max_tasks")
        return self


class StaffCreate(BaseModel):
    staff_code: NonEmpty
    name: NonEmpty
    role: StaffRole
    department: NonEmpty
    skills: list[str] = Field(default_factory=list, max_length=100)
    contacts: ContactInfo
    coverage: Coverage = Field(default_factory=Coverage)
    workload: Workload = Field(default_factory=Workload)
    active: bool = True


class StaffUpdate(BaseModel):
    name: NonEmpty | None = None
    department: NonEmpty | None = None
    skills: list[str] | None = None
    contacts: ContactInfo | None = None
    coverage: Coverage | None = None
    workload: Workload | None = None
    active: bool | None = None
