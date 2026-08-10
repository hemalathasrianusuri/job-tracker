import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from app.modules.companies.models import Company
from app.modules.jobs.enums import JobStatus, WorkMode


class Job(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "jobs"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True
    )
    company: Mapped[Company | None] = relationship("Company", lazy="selectin")

    title: Mapped[str] = mapped_column(String, nullable=False)
    location: Mapped[str | None] = mapped_column(String, nullable=True)
    work_mode: Mapped[WorkMode | None] = mapped_column(String, nullable=True)
    salary_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_max: Mapped[int | None] = mapped_column(Integer, nullable=True)

    source_url: Mapped[str | None] = mapped_column(String, nullable=True)
    raw_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Populated by the Phase 5 AI JD analyzer (skills/frameworks/experience extraction)
    parsed_requirements: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    status: Mapped[JobStatus] = mapped_column(
        String, nullable=False, default=JobStatus.WISHLIST, server_default=JobStatus.WISHLIST
    )
    referral: Mapped[bool] = mapped_column(default=False, server_default="false")
    recruiter_name: Mapped[str | None] = mapped_column(String, nullable=True)
    applied_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Populated by Phase 5's Smart Match Engine
    ats_match_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    resume_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resumes.id"), nullable=True
    )

    # 1536-dim to match OpenAI/Claude embedding models; populated in Phase 5,
    # column + index exist now so no destructive migration is needed later.
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)

    def __repr__(self) -> str:
        return f"<Job {self.title} ({self.status})>"


class JobStatusHistory(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "job_status_history"

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    from_status: Mapped[str | None] = mapped_column(String, nullable=True)
    to_status: Mapped[str] = mapped_column(String, nullable=False)
    changed_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
