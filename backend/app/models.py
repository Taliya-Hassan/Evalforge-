import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

# JSONB on Postgres, plain JSON elsewhere (lets unit tests run on SQLite)
JsonType = JSON().with_variant(JSONB(), "postgresql")


def _pk() -> Mapped[uuid.UUID]:
    return mapped_column(Uuid, primary_key=True, default=uuid.uuid4)


def _created() -> Mapped[datetime]:
    return mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        nullable=False,
    )


class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = _pk()
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = _created()


class Project(Base):
    __tablename__ = "projects"
    id: Mapped[uuid.UUID] = _pk()
    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = _created()
    __table_args__ = (UniqueConstraint("owner_id", "name", name="uq_project_owner_name"),)


class Model(Base):
    """An LLM configuration under test (e.g. provider=openai, identifier=gpt-4o, temperature)."""

    __tablename__ = "models"
    id: Mapped[uuid.UUID] = _pk()
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    provider: Mapped[str] = mapped_column(String(100))
    model_identifier: Mapped[str] = mapped_column(String(200))
    params: Mapped[dict] = mapped_column(JsonType, default=dict)
    created_at: Mapped[datetime] = _created()


class TestSuite(Base):
    __tablename__ = "test_suites"
    __test__ = False  # stop pytest trying to collect this class
    id: Mapped[uuid.UUID] = _pk()
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = _created()
    cases: Mapped[list["TestCase"]] = relationship(
        back_populates="suite", cascade="all, delete-orphan"
    )
    __table_args__ = (UniqueConstraint("project_id", "name", name="uq_suite_project_name"),)


class TestCase(Base):
    __tablename__ = "test_cases"
    __test__ = False
    id: Mapped[uuid.UUID] = _pk()
    suite_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("test_suites.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    prompt: Mapped[str] = mapped_column(Text)
    expected_output: Mapped[str | None] = mapped_column(Text)
    scorer: Mapped[str] = mapped_column(String(50), default="exact_match")
    scorer_config: Mapped[dict] = mapped_column(JsonType, default=dict)
    threshold: Mapped[float] = mapped_column(Float, default=1.0)
    created_at: Mapped[datetime] = _created()
    suite: Mapped[TestSuite] = relationship(back_populates="cases")


class Run(Base):
    __tablename__ = "runs"
    id: Mapped[uuid.UUID] = _pk()
    suite_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("test_suites.id", ondelete="CASCADE"))
    model_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("models.id"))
    triggered_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    status: Mapped[str] = mapped_column(String(20), default="queued")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = _created()
    results: Mapped[list["Result"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )
    __table_args__ = (
        CheckConstraint(
            "status IN ('queued','running','completed','failed')", name="ck_run_status"
        ),
        Index("ix_runs_suite_created", "suite_id", "created_at"),
    )


class Result(Base):
    __tablename__ = "results"
    id: Mapped[uuid.UUID] = _pk()
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("runs.id", ondelete="CASCADE"))
    test_case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("test_cases.id", ondelete="CASCADE"), index=True
    )
    output: Mapped[str | None] = mapped_column(Text)
    score: Mapped[float | None] = mapped_column(Float)
    passed: Mapped[bool | None] = mapped_column(Boolean)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = _created()
    run: Mapped[Run] = relationship(back_populates="results")
    __table_args__ = (UniqueConstraint("run_id", "test_case_id", name="uq_result_run_case"),)
