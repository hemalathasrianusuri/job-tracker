from fastapi import APIRouter
from sqlalchemy import select

from app.core.deps import CurrentUser, DbSession
from app.modules.companies.models import Company
from app.modules.companies.schemas import CompanyRead

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("", response_model=list[CompanyRead])
async def search_companies(db: DbSession, _current_user: CurrentUser, q: str = "", limit: int = 10):
    """Autocomplete lookup for the job-creation form. Companies are a shared
    lookup table (not user-scoped), so any authenticated user can search them —
    the data itself is non-sensitive (just names/domains)."""
    stmt = select(Company).limit(min(limit, 25))
    if q:
        stmt = stmt.where(Company.name.ilike(f"%{q}%"))
    result = await db.execute(stmt)
    return result.scalars().all()
