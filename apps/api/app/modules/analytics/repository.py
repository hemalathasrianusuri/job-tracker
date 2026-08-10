import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.companies.models import Company
from app.modules.jobs.models import Job
from app.modules.skills.models import JobSkill, Skill


class AnalyticsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_status_counts(self, user_id: uuid.UUID) -> dict[str, int]:
        result = await self.db.execute(
            select(Job.status, func.count())
            .where(Job.user_id == user_id, Job.deleted_at.is_(None))
            .group_by(Job.status)
        )
        return {status: count for status, count in result.all()}

    async def get_avg_ats_score(self, user_id: uuid.UUID) -> float | None:
        result = await self.db.execute(
            select(func.avg(Job.ats_match_score)).where(
                Job.user_id == user_id, Job.deleted_at.is_(None), Job.ats_match_score.is_not(None)
            )
        )
        avg = result.scalar_one_or_none()
        return round(float(avg), 1) if avg is not None else None

    async def get_distinct_company_count(self, user_id: uuid.UUID) -> int:
        result = await self.db.execute(
            select(func.count(func.distinct(Job.company_id))).where(
                Job.user_id == user_id, Job.deleted_at.is_(None), Job.company_id.is_not(None)
            )
        )
        return result.scalar_one()

    async def get_top_skills(self, user_id: uuid.UUID, limit: int = 50) -> list[tuple[str, str, int]]:
        """Demand analytics: how often each skill appears across the user's OWN
        saved jobs. This is intentionally scoped per-user, not global — with a
        single Postgres instance and no cross-tenant job corpus yet, a global
        'market demand' number would just be one person's job search, which
        would be misleading to present as market data. Revisit if/when the
        corpus is large enough to be a meaningful aggregate (see Phase 1's
        note on descoped multi-source job discovery)."""
        result = await self.db.execute(
            select(Skill.name, Skill.category, func.count(JobSkill.job_id).label("cnt"))
            .join(JobSkill, JobSkill.skill_id == Skill.id)
            .join(Job, Job.id == JobSkill.job_id)
            .where(Job.user_id == user_id, Job.deleted_at.is_(None))
            .group_by(Skill.name, Skill.category)
            .order_by(func.count(JobSkill.job_id).desc())
            .limit(limit)
        )
        return result.all()

    async def get_top_companies(self, user_id: uuid.UUID, limit: int = 20) -> list[tuple[str, int]]:
        result = await self.db.execute(
            select(Company.name, func.count(Job.id).label("cnt"))
            .join(Job, Job.company_id == Company.id)
            .where(Job.user_id == user_id, Job.deleted_at.is_(None))
            .group_by(Company.name)
            .order_by(func.count(Job.id).desc())
            .limit(limit)
        )
        return result.all()
