import uuid
from typing import Literal

from app.modules.companies.repository import CompanyRepository
from app.modules.discovery.adapters.ashby import fetch_ashby_jobs
from app.modules.discovery.adapters.greenhouse import fetch_greenhouse_jobs
from app.modules.discovery.adapters.lever import fetch_lever_jobs
from app.modules.discovery.adapters.url_import import fetch_job_from_url
from app.modules.discovery.schemas import DiscoveredJob
from app.modules.jobs.models import Job
from app.modules.jobs.repository import JobRepository
from app.modules.jobs.schemas import JobCreate

SourceName = Literal["greenhouse", "lever", "ashby"]

_FETCHERS = {
    "greenhouse": fetch_greenhouse_jobs,
    "lever": fetch_lever_jobs,
    "ashby": fetch_ashby_jobs,
}


class DiscoveryService:
    def __init__(self, job_repo: JobRepository, company_repo: CompanyRepository):
        self.job_repo = job_repo
        self.company_repo = company_repo

    async def search(self, source: SourceName, company_slug: str) -> list[DiscoveredJob]:
        fetcher = _FETCHERS[source]
        return await fetcher(company_slug)

    async def import_from_url(self, url: str) -> DiscoveredJob:
        return await fetch_job_from_url(url)

    async def save_discovered_job(self, *, user_id: uuid.UUID, discovered: DiscoveredJob) -> Job:
        """Imports a DiscoveredJob as a tracked job in 'wishlist' status — the
        user still reviews and decides to apply; nothing here submits an
        application on their behalf."""
        company = await self.company_repo.get_or_create(discovered.company_name)
        job = await self.job_repo.create(
            user_id=user_id,
            company_id=company.id,
            payload=JobCreate(
                company_name=discovered.company_name,
                title=discovered.title,
                location=discovered.location,
                source_url=discovered.url,
                raw_description=discovered.raw_description,
            ),
        )
        await self.job_repo.add_status_history(
            job_id=job.id, from_status=None, to_status=job.status,
            notes=f"Imported from {discovered.source}",
        )
        job.company = company
        return job
