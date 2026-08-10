import uuid

from fastapi import APIRouter, HTTPException, Query, status

from app.core.deps import CurrentUser, DbSession
from app.modules.companies.repository import CompanyRepository
from app.modules.jobs.enums import JobStatus
from app.modules.jobs.repository import ALLOWED_SORT_FIELDS, JobRepository
from app.modules.jobs.schemas import (
    JobCreate,
    JobRead,
    JobStatusHistoryRead,
    JobStatusUpdate,
    JobUpdate,
    PaginatedJobs,
)
from app.modules.jobs.service import JobNotFoundError, JobService

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _service(db: DbSession) -> JobService:
    return JobService(JobRepository(db), CompanyRepository(db))


@router.post("", response_model=JobRead, status_code=status.HTTP_201_CREATED)
async def create_job(payload: JobCreate, db: DbSession, current_user: CurrentUser):
    job = await _service(db).create_job(user_id=current_user.id, payload=payload)
    await db.commit()
    return job


@router.get("", response_model=PaginatedJobs)
async def list_jobs(
    db: DbSession,
    current_user: CurrentUser,
    status_filter: JobStatus | None = Query(default=None, alias="status"),
    company_id: uuid.UUID | None = None,
    search: str | None = Query(default=None, max_length=200),
    sort_by: str = Query(default="created_at"),
    sort_desc: bool = True,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    if sort_by not in ALLOWED_SORT_FIELDS:
        raise HTTPException(status_code=400, detail=f"sort_by must be one of {list(ALLOWED_SORT_FIELDS)}")

    items, total = await _service(db).list_jobs(
        user_id=current_user.id,
        status=status_filter,
        company_id=company_id,
        search=search,
        sort_by=sort_by,
        sort_desc=sort_desc,
        page=page,
        page_size=page_size,
    )
    return PaginatedJobs(items=items, total=total, page=page, page_size=page_size)


@router.get("/{job_id}", response_model=JobRead)
async def get_job(job_id: uuid.UUID, db: DbSession, current_user: CurrentUser):
    try:
        return await _service(db).get_job_or_404(job_id=job_id, user_id=current_user.id)
    except JobNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.patch("/{job_id}", response_model=JobRead)
async def update_job(job_id: uuid.UUID, payload: JobUpdate, db: DbSession, current_user: CurrentUser):
    service = _service(db)
    try:
        job = await service.get_job_or_404(job_id=job_id, user_id=current_user.id)
    except JobNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    job = await service.update_job(job=job, payload=payload)
    await db.commit()
    return job


@router.patch("/{job_id}/status", response_model=JobRead)
async def update_job_status(
    job_id: uuid.UUID, payload: JobStatusUpdate, db: DbSession, current_user: CurrentUser
):
    """Separate from the general PATCH so every status change is guaranteed to
    produce a job_status_history row — the general update endpoint can't
    silently change status and skip the audit trail."""
    service = _service(db)
    try:
        job = await service.get_job_or_404(job_id=job_id, user_id=current_user.id)
    except JobNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    job = await service.update_status(job=job, payload=payload)
    await db.commit()
    return job


@router.get("/{job_id}/history", response_model=list[JobStatusHistoryRead])
async def get_job_status_history(job_id: uuid.UUID, db: DbSession, current_user: CurrentUser):
    service = _service(db)
    try:
        await service.get_job_or_404(job_id=job_id, user_id=current_user.id)  # ownership check
    except JobNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return await JobRepository(db).get_status_history(job_id)


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(job_id: uuid.UUID, db: DbSession, current_user: CurrentUser):
    service = _service(db)
    try:
        job = await service.get_job_or_404(job_id=job_id, user_id=current_user.id)
    except JobNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    await service.delete_job(job=job)
    await db.commit()
