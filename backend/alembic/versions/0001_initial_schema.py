"""initial schema

Revision ID: 0001
Revises:
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

NOW = sa.text("now()")


def _id():
    return sa.Column("id", sa.Uuid(), primary_key=True)


def _created():
    return sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False)


def upgrade() -> None:
    op.create_table(
        "users",
        _id(),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        _created(),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "projects",
        _id(),
        sa.Column("owner_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text()),
        _created(),
        sa.UniqueConstraint("owner_id", "name", name="uq_project_owner_name"),
    )
    op.create_index("ix_projects_owner_id", "projects", ["owner_id"])

    op.create_table(
        "models",
        _id(),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("provider", sa.String(100), nullable=False),
        sa.Column("model_identifier", sa.String(200), nullable=False),
        sa.Column("params", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        _created(),
    )
    op.create_index("ix_models_project_id", "models", ["project_id"])

    op.create_table(
        "test_suites",
        _id(),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text()),
        _created(),
        sa.UniqueConstraint("project_id", "name", name="uq_suite_project_name"),
    )
    op.create_index("ix_test_suites_project_id", "test_suites", ["project_id"])

    op.create_table(
        "test_cases",
        _id(),
        sa.Column("suite_id", sa.Uuid(), sa.ForeignKey("test_suites.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("expected_output", sa.Text()),
        sa.Column("scorer", sa.String(50), nullable=False, server_default="exact_match"),
        sa.Column("scorer_config", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("threshold", sa.Float(), nullable=False, server_default="1.0"),
        _created(),
    )
    op.create_index("ix_test_cases_suite_id", "test_cases", ["suite_id"])

    op.create_table(
        "runs",
        _id(),
        sa.Column("suite_id", sa.Uuid(), sa.ForeignKey("test_suites.id", ondelete="CASCADE"), nullable=False),
        sa.Column("model_id", sa.Uuid(), sa.ForeignKey("models.id"), nullable=False),
        sa.Column("triggered_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("status", sa.String(20), nullable=False, server_default="queued"),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        _created(),
        sa.CheckConstraint("status IN ('queued','running','completed','failed')", name="ck_run_status"),
    )
    op.create_index("ix_runs_suite_created", "runs", ["suite_id", "created_at"])

    op.create_table(
        "results",
        _id(),
        sa.Column("run_id", sa.Uuid(), sa.ForeignKey("runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("test_case_id", sa.Uuid(), sa.ForeignKey("test_cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("output", sa.Text()),
        sa.Column("score", sa.Float()),
        sa.Column("passed", sa.Boolean()),
        sa.Column("latency_ms", sa.Integer()),
        sa.Column("error", sa.Text()),
        _created(),
        sa.UniqueConstraint("run_id", "test_case_id", name="uq_result_run_case"),
    )
    op.create_index("ix_results_test_case_id", "results", ["test_case_id"])


def downgrade() -> None:
    for table in ("results", "runs", "test_cases", "test_suites", "models", "projects", "users"):
        op.drop_table(table)
