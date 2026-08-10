import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.companies.schemas import CompanyRead
from app.modules.jobs.enums import JobStatus, WorkMode


class JobCreate(BaseModel):
    # Free-text company name — the service layer resolves this to a Company
    # row via get_or_create, so the frontend never needs to know company IDs.
    company_name: str = Field(min_length=1, max_length=200)
    title: str = Field(min_length=1, max_length=200)
    location: str | None = None
    work_mode: WorkMode | None = None
    salary_min: int | None = Field(default=None, ge=0)
    salary_max: int | None = Field(default=None, ge=0)
    source_url: str | None = None
    raw_description: str | None = None
    referral: bool = False
    recruiter_name: str | None = None
    status: JobStatus = JobStatus.WISHLIST


class JobUpdate(BaseModel):
    """All fields optional — PATCH semantics. Status changes go through the
    dedicated /jobs/{id}/status endpoint instead, so they're excluded here and
    always produce a job_status_history row."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    location: str | None = None
    work_mode: WorkMode | None = None
    salary_min: int | None = Field(default=None, ge=0)
    salary_max: int | None = Field(default=None, ge=0)
    source_url: str | None = None
    raw_description: str | None = None
    referral: bool | None = None
    recruiter_name: str | None = None
    resume_id: uuid.UUID | None = None


class JobStatusUpdate(BaseModel):
    status: JobStatus
    notes: str | None = None


class JobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company: CompanyRead | None
    title: str
    location: str | None
    work_mode: WorkMode | None
    salary_min: int | None
    salary_max: int | None
    source_url: str | None
    status: JobStatus
    referral: bool
    recruiter_name: str | None
    applied_at: datetime | None
    ats_match_score: float | None
    resume_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class JobStatusHistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    from_status: str | None
    to_status: str
    changed_at: datetime
    notes: str | None


class PaginatedJobs(BaseModel):
    items: list[JobRead]
    total: int
    page: int
    page_size: int
