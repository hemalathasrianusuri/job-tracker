import uuid
from datetime import datetime, timezone

from app.modules.companies.repository import CompanyRepository
from app.modules.jobs.enums import JobStatus
from app.modules.jobs.models import Job
from app.modules.jobs.repository import JobRepository
from app.modules.jobs.schemas import JobCreate, JobStatusUpdate, JobUpdate


class JobNotFoundError(Exception):
    pass


class JobService:
    def __init__(self, job_repo: JobRepository, company_repo: CompanyRepository):
        self.job_repo = job_repo
        self.company_repo = company_repo

    async def create_job(self, *, user_id: uuid.UUID, payload: JobCreate) -> Job:
        company = await self.company_repo.get_or_create(payload.company_name)
        job = await self.job_repo.create(user_id=user_id, company_id=company.id, payload=payload)

        # The initial status is itself a transition worth recording — otherwise
        # "time in wishlist before applying" can't be computed later.
        await self.job_repo.add_status_history(
            job_id=job.id, from_status=None, to_status=job.status, notes="Job created"
        )
        job.company = company
        return job

    async def get_job_or_404(self, *, job_id: uuid.UUID, user_id: uuid.UUID) -> Job:
        job = await self.job_repo.get_by_id(job_id, user_id)
        if job is None:
            raise JobNotFoundError(f"Job {job_id} not found")
        return job

    async def update_job(self, *, job: Job, payload: JobUpdate) -> Job:
        return await self.job_repo.apply_update(job, payload)

    async def delete_job(self, *, job: Job) -> None:
        await self.job_repo.soft_delete(job)

    async def update_status(self, *, job: Job, payload: JobStatusUpdate) -> Job:
        previous_status = job.status
        job.status = payload.status

        # First time the job leaves WISHLIST, stamp applied_at — this drives
        # the "days since applied" and response-rate analytics in Phase 6.
        if previous_status == JobStatus.WISHLIST and payload.status != JobStatus.WISHLIST and job.applied_at is None:
            job.applied_at = datetime.now(timezone.utc)

        await self.job_repo.add_status_history(
            job_id=job.id, from_status=previous_status, to_status=payload.status, notes=payload.notes
        )
        return job

    async def list_jobs(self, **kwargs):
        return await self.job_repo.list_for_user(**kwargs)
