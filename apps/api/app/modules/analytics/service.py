import uuid

from app.modules.analytics.repository import AnalyticsRepository
from app.modules.analytics.schemas import (
    CompanyDemandItem,
    DashboardSummary,
    DemandAnalytics,
    SkillDemandItem,
    StatusBreakdownItem,
)
from app.modules.jobs.enums import TERMINAL_STATUSES, JobStatus


class AnalyticsService:
    def __init__(self, repo: AnalyticsRepository):
        self.repo = repo

    async def get_dashboard_summary(self, user_id: uuid.UUID) -> DashboardSummary:
        counts = await self.repo.get_status_counts(user_id)
        total = sum(counts.values())

        active = sum(c for s, c in counts.items() if JobStatus(s) not in TERMINAL_STATUSES)
        offers = counts.get(JobStatus.OFFER, 0)
        accepted = counts.get(JobStatus.ACCEPTED, 0)
        rejected = counts.get(JobStatus.REJECTED, 0)
        withdrawn = counts.get(JobStatus.WITHDRAWN, 0)
        ghosted = counts.get(JobStatus.GHOSTED, 0)

        # Response rate: of everything that moved past a bare application,
        # what fraction actually got a response (left APPLIED for anything
        # other than staying there)? wishlist entries aren't "applications"
        # yet, so they're excluded from the denominator.
        applied_or_later = total - counts.get(JobStatus.WISHLIST, 0)
        responded = applied_or_later - counts.get(JobStatus.APPLIED, 0)
        response_rate = round((responded / applied_or_later) * 100, 1) if applied_or_later > 0 else 0.0

        return DashboardSummary(
            total_applications=total,
            active_pipeline=active,
            offers=offers,
            accepted=accepted,
            rejected=rejected,
            withdrawn=withdrawn,
            ghosted=ghosted,
            response_rate_pct=response_rate,
            avg_ats_match_score=await self.repo.get_avg_ats_score(user_id),
            companies_applied=await self.repo.get_distinct_company_count(user_id),
            status_breakdown=[StatusBreakdownItem(status=s, count=c) for s, c in counts.items()],
        )

    async def get_demand_analytics(self, user_id: uuid.UUID) -> DemandAnalytics:
        skill_rows = await self.repo.get_top_skills(user_id)
        company_rows = await self.repo.get_top_companies(user_id)

        top_skills = [SkillDemandItem(skill=name, category=cat, job_count=cnt) for name, cat, cnt in skill_rows]

        by_category: dict[str, list[SkillDemandItem]] = {}
        for item in top_skills:
            by_category.setdefault(item.category, []).append(item)

        return DemandAnalytics(
            top_skills=top_skills,
            top_companies=[CompanyDemandItem(company=name, job_count=cnt) for name, cnt in company_rows],
            skills_by_category=by_category,
        )
