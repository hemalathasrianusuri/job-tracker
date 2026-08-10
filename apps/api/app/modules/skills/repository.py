import uuid

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.skills.models import JobSkill, Skill, UserSkill


class SkillRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create(self, name: str, category: str) -> Skill:
        result = await self.db.execute(select(Skill).where(func.lower(Skill.name) == name.strip().lower()))
        existing = result.scalar_one_or_none()
        if existing:
            return existing

        skill = Skill(name=name.strip(), category=category)
        self.db.add(skill)
        await self.db.flush()
        await self.db.refresh(skill)
        return skill

    async def replace_job_skills(self, *, job_id: uuid.UUID, skill_ids: list[uuid.UUID]) -> None:
        """Re-running JD analysis (e.g. after a posting edit) shouldn't accumulate
        duplicate rows — clear and re-insert rather than diffing, since job_skills
        has no independent identity worth preserving across re-analyses."""
        await self.db.execute(JobSkill.__table__.delete().where(JobSkill.job_id == job_id))
        for skill_id in skill_ids:
            stmt = pg_insert(JobSkill).values(job_id=job_id, skill_id=skill_id).on_conflict_do_nothing()
            await self.db.execute(stmt)
        await self.db.flush()


class UserSkillRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def upsert(self, *, user_id: uuid.UUID, skill_id: uuid.UUID, proficiency: str, source: str) -> None:
        stmt = (
            pg_insert(UserSkill)
            .values(user_id=user_id, skill_id=skill_id, proficiency=proficiency, source=source)
            .on_conflict_do_update(
                index_elements=[UserSkill.user_id, UserSkill.skill_id],
                set_={"proficiency": proficiency, "source": source},
            )
        )
        await self.db.execute(stmt)
        await self.db.flush()
