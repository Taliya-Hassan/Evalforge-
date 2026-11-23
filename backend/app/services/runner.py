"""Executes a run: calls the model for each test case, scores it, stores a Result."""

import time
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from app.models import Model, Result, Run, TestCase
from app.services import providers, scorers


def _now() -> datetime:
    return datetime.now(UTC)


def _run_case(run_id: uuid.UUID, model: Model, case: TestCase) -> Result:
    res = Result(run_id=run_id, test_case_id=case.id)
    start = time.perf_counter()
    try:
        output = providers.generate(model, case.prompt)
        res.latency_ms = int((time.perf_counter() - start) * 1000)
        res.output = output
        res.score = scorers.score_case(
            case, output, judge=lambda prompt: providers.generate(model, prompt)
        )
        res.passed = res.score >= case.threshold
    except Exception as exc:  # one bad case must never abort the run
        res.latency_ms = int((time.perf_counter() - start) * 1000)
        res.error = f"{type(exc).__name__}: {exc}"[:1000]
        res.score = 0.0
        res.passed = False
    return res


def execute_run(run_id: uuid.UUID, session_factory: sessionmaker) -> None:
    with session_factory() as db:
        run = db.get(Run, run_id)
        if run is None:
            return
        run.status = "running"
        run.started_at = _now()
        db.commit()
        try:
            model = db.get(Model, run.model_id)
            cases = db.scalars(
                select(TestCase)
                .where(TestCase.suite_id == run.suite_id)
                .order_by(TestCase.created_at, TestCase.name)
            ).all()
            for case in cases:
                db.add(_run_case(run.id, model, case))
                db.commit()
            run.status = "completed"
        except Exception:
            db.rollback()
            run.status = "failed"
        run.finished_at = _now()
        db.commit()
