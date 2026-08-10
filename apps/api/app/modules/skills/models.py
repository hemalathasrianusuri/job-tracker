import uuid

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.schema import CheckConstraint

from app.db.base import Base, UUIDPrimaryKeyMixin

SKILL_CATEGORIES = {"language", "framework", "cloud", "database", "devops", "soft_skill", "ai_ml", "other"}


class Skill(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "skills"
    __table_args__ = (CheckConstraint(f"category IN {tuple(SKILL_CATEGORIES)}", name="ck_skills_category"),)

    name: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    category: Mapped[str] = mapped_column(String, nullable=False)


class JobSkill(Base):
    __tablename__ = "job_skills"

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), primary_key=True
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True
    )
    importance: Mapped[float] = mapped_column(Numeric(3, 2), default=1.0, server_default="1.0")


class UserSkill(Base):
    __tablename__ = "user_skills"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True
    )
    proficiency: Mapped[str] = mapped_column(String, nullable=False)  # learning | comfortable | strong
    source: Mapped[str] = mapped_column(String, nullable=False)  # resume | manual


class SkillPrerequisite(Base):
    """Adjacency list forming the skill knowledge graph — e.g. (Celery, requires: Redis)
    lets the Phase 6 learning engine sequence roadmaps instead of ordering resources
    arbitrarily. No separate graph DB; this is cheap enough in Postgres at this scale."""

    __tablename__ = "skill_prerequisites"

    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True
    )
    prerequisite_skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True
    )
