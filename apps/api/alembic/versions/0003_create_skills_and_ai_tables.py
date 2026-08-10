"""create skills taxonomy, ai usage log, generated documents, interview questions

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-19

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "skills",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                   server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(), nullable=False, unique=True),
        sa.Column("category", sa.String(), nullable=False),
        sa.CheckConstraint(
            "category IN ('language','framework','cloud','database','devops','soft_skill','ai_ml','other')",
            name="ck_skills_category",
        ),
    )
    op.create_index("ix_skills_name", "skills", ["name"])

    op.create_table(
        "job_skills",
        sa.Column("job_id", postgresql.UUID(as_uuid=True),
                   sa.ForeignKey("jobs.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("skill_id", postgresql.UUID(as_uuid=True),
                   sa.ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("importance", sa.Numeric(3, 2), server_default="1.0", nullable=False),
    )

    op.create_table(
        "user_skills",
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                   sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("skill_id", postgresql.UUID(as_uuid=True),
                   sa.ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("proficiency", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
    )

    op.create_table(
        "skill_prerequisites",
        sa.Column("skill_id", postgresql.UUID(as_uuid=True),
                   sa.ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("prerequisite_skill_id", postgresql.UUID(as_uuid=True),
                   sa.ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "ai_usage_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                   server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                   sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("operation", sa.String(), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False),
        sa.Column("output_tokens", sa.Integer(), nullable=False),
        sa.Column("estimated_cost_usd", sa.Numeric(10, 5), nullable=False),
        sa.Column("cache_hit", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_ai_usage_log_user_id", "ai_usage_log", ["user_id"])
    op.create_index("ix_ai_usage_log_operation", "ai_usage_log", ["operation"])

    op.create_table(
        "generated_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                   server_default=sa.text("gen_random_uuid()")),
        sa.Column("job_id", postgresql.UUID(as_uuid=True),
                   sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("doc_type", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("model_used", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_generated_documents_job_id", "generated_documents", ["job_id"])

    op.create_table(
        "interview_questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                   server_default=sa.text("gen_random_uuid()")),
        sa.Column("job_id", postgresql.UUID(as_uuid=True),
                   sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("suggested_answer_notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_interview_questions_job_id", "interview_questions", ["job_id"])


def downgrade() -> None:
    op.drop_table("interview_questions")
    op.drop_table("generated_documents")
    op.drop_table("ai_usage_log")
    op.drop_table("skill_prerequisites")
    op.drop_table("user_skills")
    op.drop_table("job_skills")
    op.drop_index("ix_skills_name", table_name="skills")
    op.drop_table("skills")
