from fastapi import APIRouter, HTTPException, status

from app.core.deps import CurrentUser, DbSession
from app.modules.companies.repository import CompanyRepository
from app.modules.discovery.schemas import DiscoveredJob, ImportJobRequest, ImportUrlRequest
from app.modules.discovery.service import DiscoveryService, SourceName
from app.modules.jobs.repository import JobRepository
from app.modules.jobs.schemas import JobRead

router = APIRouter(prefix="/discovery", tags=["discovery"])


def _service(db: DbSession) -> DiscoveryService:
    return DiscoveryService(JobRepository(db), CompanyRepository(db))


@router.get("/search", response_model=list[DiscoveredJob])
async def search_job_board(
    source: SourceName, company: str, db: DbSession, _current_user: CurrentUser
):
    """Searches a company's public job board. `company` is that board's slug —
    e.g. for Greenhouse, the value in boards.greenhouse.io/<slug>."""
    try:
        return await _service(db).search(source, company)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Couldn't reach {source}'s job board for '{company}': {exc}",
        )


@router.post("/import-url", response_model=DiscoveredJob)
async def fetch_from_url(payload: ImportUrlRequest, db: DbSession, _current_user: CurrentUser):
    """Fetches a user-pasted job posting URL and extracts text — the fallback
    for any board without a public API. Returns a DiscoveredJob for the user
    to review before saving via POST /discovery/import (two-step so the user
    can fix the auto-extracted title/company before it's tracked)."""
    try:
        return await _service(db).import_from_url(payload.url)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))


@router.post("/import", response_model=JobRead, status_code=status.HTTP_201_CREATED)
async def import_discovered_job(payload: ImportJobRequest, db: DbSession, current_user: CurrentUser):
    job = await _service(db).save_discovered_job(user_id=current_user.id, discovered=payload.job)
    await db.commit()
    return job
