import uuid

from sqlalchemy import Boolean, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class Resume(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "resumes"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    file_url: Mapped[str] = mapped_column(String, nullable=False)
    original_filename: Mapped[str] = mapped_column(String, nullable=False)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Populated by the Phase 5 AI resume parser: skills, experience, education
    parsed_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_master: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    # Populated by the Phase 5 AI Resume Optimizer
    ats_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)

    def __repr__(self) -> str:
        return f"<Resume {self.original_filename}>"
