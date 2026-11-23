import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

Provider = Literal["mock", "openai", "anthropic"]
Scorer = Literal["exact_match", "contains", "regex", "llm_judge"]


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---- auth ----
class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(ORM):
    id: uuid.UUID
    email: EmailStr
    created_at: datetime


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---- projects / models ----
class ProjectIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None


class ProjectOut(ORM):
    id: uuid.UUID
    name: str
    description: str | None
    created_at: datetime


class ModelIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    provider: Provider
    model_identifier: str = Field(min_length=1, max_length=200)
    params: dict[str, Any] = {}


class ModelOut(ORM):
    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    provider: str
    model_identifier: str
    params: dict[str, Any]
    created_at: datetime


# ---- suites / cases ----
class SuiteIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None


class SuiteOut(ORM):
    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    description: str | None
    created_at: datetime


class CaseIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    prompt: str = Field(min_length=1)
    expected_output: str | None = None
    scorer: Scorer = "exact_match"
    scorer_config: dict[str, Any] = {}
    threshold: float = Field(default=1.0, ge=0.0, le=1.0)


class CaseOut(ORM):
    id: uuid.UUID
    suite_id: uuid.UUID
    name: str
    prompt: str
    expected_output: str | None
    scorer: str
    scorer_config: dict[str, Any]
    threshold: float


# ---- runs ----
class RunCreate(BaseModel):
    model_id: uuid.UUID


class RunOut(ORM):
    id: uuid.UUID
    suite_id: uuid.UUID
    model_id: uuid.UUID
    status: str
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None


class ResultOut(BaseModel):
    test_case_id: uuid.UUID
    test_case_name: str
    output: str | None
    score: float | None
    passed: bool | None
    latency_ms: int | None
    error: str | None


class RunSummary(BaseModel):
    total: int
    passed: int
    failed: int
    errors: int
    pass_rate: float
    mean_score: float
    latency_p50_ms: int | None
    latency_p95_ms: int | None


class RunDetail(RunOut):
    summary: RunSummary
    results: list[ResultOut]


# ---- diff ----
class DiffItem(BaseModel):
    test_case_id: uuid.UUID
    name: str
    prompt: str
    status: Literal["regressed", "improved", "unchanged", "new", "missing"]
    baseline_passed: bool | None
    candidate_passed: bool | None
    baseline_score: float | None
    candidate_score: float | None
    score_delta: float | None
    baseline_output: str | None
    candidate_output: str | None
    baseline_error: str | None
    candidate_error: str | None


class DiffOut(BaseModel):
    suite_id: uuid.UUID
    baseline_run_id: uuid.UUID
    candidate_run_id: uuid.UUID
    counts: dict[str, int]
    baseline_pass_rate: float
    candidate_pass_rate: float
    pass_rate_delta: float
    items: list[DiffItem]
