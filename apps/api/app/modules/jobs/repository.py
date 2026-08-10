import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.jobs.enums import JobStatus
from app.modules.jobs.models import Job, JobStatusHistory
from app.modules.jobs.schemas import JobCreate, JobUpdate

ALLOWED_SORT_FIELDS = {
    "created_at": Job.created_at,
    "updated_at": Job.updated_at,
    "applied_at": Job.applied_at,
    "title": Job.title,
    "ats_match_score": Job.ats_match_score,
}


class JobRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, job_id: uuid.UUID, user_id: uuid.UUID) -> Job | None:
        result = await self.db.execute(
            select(Job).where(Job.id == job_id, Job.user_id == user_id, Job.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def create(self, *, user_id: uuid.UUID, company_id: uuid.UUID, payload: JobCreate) -> Job:
        job = Job(
            user_id=user_id,
            company_id=company_id,
            title=payload.title,
            location=payload.location,
            work_mode=payload.work_mode,
            salary_min=payload.salary_min,
            salary_max=payload.salary_max,
            source_url=payload.source_url,
            raw_description=payload.raw_description,
            referral=payload.referral,
            recruiter_name=payload.recruiter_name,
            status=payload.status,
            applied_at=datetime.now(timezone.utc) if payload.status != JobStatus.WISHLIST else None,
        )
        self.db.add(job)
        await self.db.flush()
        await self.db.refresh(job)
        return job

    async def apply_update(self, job: Job, payload: JobUpdate) -> Job:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(job, field, value)
        await self.db.flush()
        return job

    async def soft_delete(self, job: Job) -> None:
        job.deleted_at = datetime.now(timezone.utc)
        await self.db.flush()

    async def list_for_user(
        self,
        *,
        user_id: uuid.UUID,
        status: JobStatus | None,
        company_id: uuid.UUID | None,
        search: str | None,
        sort_by: str,
        sort_desc: bool,
        page: int,
        page_size: int,
    ) -> tuple[list[Job], int]:
        conditions = [Job.user_id == user_id, Job.deleted_at.is_(None)]
        if status:
            conditions.append(Job.status == status)
        if company_id:
            conditions.append(Job.company_id == company_id)
        if search:
            conditions.append(Job.title.ilike(f"%{search}%"))

        base_stmt = select(Job).where(*conditions)

        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total = (await self.db.execute(count_stmt)).scalar_one()

        sort_column = ALLOWED_SORT_FIELDS.get(sort_by, Job.created_at)
        order = sort_column.desc() if sort_desc else sort_column.asc()

        stmt = base_stmt.order_by(order).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def add_status_history(
        self, *, job_id: uuid.UUID, from_status: str | None, to_status: str, notes: str | None
    ) -> None:
        self.db.add(
            JobStatusHistory(job_id=job_id, from_status=from_status, to_status=to_status, notes=notes)
        )
        await self.db.flush()

    async def get_status_history(self, job_id: uuid.UUID) -> list[JobStatusHistory]:
        result = await self.db.execute(
            select(JobStatusHistory)
            .where(JobStatusHistory.job_id == job_id)
            .order_by(JobStatusHistory.changed_at.asc())
        )
        return list(result.scalars().all())
