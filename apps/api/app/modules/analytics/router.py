from fastapi import APIRouter

from app.core.deps import CurrentUser, DbSession
from app.modules.analytics.repository import AnalyticsRepository
from app.modules.analytics.schemas import DashboardSummary, DemandAnalytics
from app.modules.analytics.service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _service(db: DbSession) -> AnalyticsService:
    return AnalyticsService(AnalyticsRepository(db))


@router.get("/summary", response_model=DashboardSummary)
async def get_summary(db: DbSession, current_user: CurrentUser):
    """Backs the Phase 4 dashboard — replaces the client-side count-every-row
    approach with a server-side aggregate that scales past a couple hundred jobs."""
    return await _service(db).get_dashboard_summary(current_user.id)


@router.get("/demand", response_model=DemandAnalytics)
async def get_demand(db: DbSession, current_user: CurrentUser):
    """Top skills/frameworks/companies across the user's own saved jobs."""
    return await _service(db).get_demand_analytics(current_user.id)
