import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from app.db import get_db
from app.deps import get_current_user, owned_run, owned_suite
from app.models import Model, Result, Run, TestCase, TestSuite, User
from app.schemas import DiffOut, ResultOut, RunCreate, RunDetail, RunOut
from app.services.diff import build_diff
from app.services.runner import execute_run
from app.services.stats import summarize

router = APIRouter(tags=["runs"])


@router.post("/suites/{suite_id}/runs", response_model=RunOut, status_code=status.HTTP_202_ACCEPTED)
def create_run(
    body: RunCreate,
    background: BackgroundTasks,
    suite: TestSuite = Depends(owned_suite),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    model = db.get(Model, body.model_id)
    if model is None or model.project_id != suite.project_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Model not found in this project")
    n_cases = db.scalar(
        select(func.count()).select_from(TestCase).where(TestCase.suite_id == suite.id)
    )
    if not n_cases:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Suite has no test cases")
    run = Run(suite_id=suite.id, model_id=model.id, triggered_by=user.id, status="queued")
    db.add(run)
    db.commit()
    factory = sessionmaker(bind=db.get_bind(), expire_on_commit=False)
    background.add_task(execute_run, run.id, factory)
    return run


@router.get("/suites/{suite_id}/runs", response_model=list[RunOut])
def list_runs(suite: TestSuite = Depends(owned_suite), db: Session = Depends(get_db)):
    q = select(Run).where(Run.suite_id == suite.id).order_by(Run.created_at.desc())
    return db.scalars(q).all()


def _results_with_cases(db: Session, run_id: uuid.UUID) -> list[tuple[Result, TestCase]]:
    q = (
        select(Result, TestCase)
        .join(TestCase, TestCase.id == Result.test_case_id)
        .where(Result.run_id == run_id)
        .order_by(TestCase.created_at, TestCase.name)
    )
    return [(r, c) for r, c in db.execute(q).all()]


@router.get("/runs/{run_id}", response_model=RunDetail)
def get_run(run: Run = Depends(owned_run), db: Session = Depends(get_db)):
    rows = _results_with_cases(db, run.id)
    results = [
        ResultOut(
            test_case_id=c.id,
            test_case_name=c.name,
            output=r.output,
            score=r.score,
            passed=r.passed,
            latency_ms=r.latency_ms,
            error=r.error,
        )
        for r, c in rows
    ]
    base = RunOut.model_validate(run).model_dump()
    return RunDetail(**base, summary=summarize(r for r, _ in rows), results=results)


@router.get("/suites/{suite_id}/diff", response_model=DiffOut)
def diff_runs(
    baseline: uuid.UUID | None = Query(default=None),
    candidate: uuid.UUID | None = Query(default=None),
    suite: TestSuite = Depends(owned_suite),
    db: Session = Depends(get_db),
):
    """Compare two runs. With no params, compares the latest two completed runs."""
    if (baseline is None) != (candidate is None):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Pass both baseline and candidate, or neither"
        )
    if baseline is None:
        q = (
            select(Run)
            .where(Run.suite_id == suite.id, Run.status == "completed")
            .order_by(Run.created_at.desc())
            .limit(2)
        )
        latest = db.scalars(q).all()
        if len(latest) < 2:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Need at least two completed runs")
        candidate, baseline = latest[0].id, latest[1].id
    for rid in (baseline, candidate):
        run = db.get(Run, rid)
        if run is None or run.suite_id != suite.id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Run not found in this suite")

    cases = db.scalars(
        select(TestCase).where(TestCase.suite_id == suite.id).order_by(TestCase.created_at)
    ).all()
    base_results = db.scalars(select(Result).where(Result.run_id == baseline)).all()
    cand_results = db.scalars(select(Result).where(Result.run_id == candidate)).all()
    data = build_diff(cases, base_results, cand_results)
    return DiffOut(
        suite_id=suite.id, baseline_run_id=baseline, candidate_run_id=candidate, **data
    )
