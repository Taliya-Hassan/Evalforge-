from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import commit_or_409, owned_case, owned_project, owned_suite
from app.models import Project, TestCase, TestSuite
from app.schemas import CaseIn, CaseOut, SuiteIn, SuiteOut

router = APIRouter(tags=["suites"])


@router.get("/projects/{project_id}/suites", response_model=list[SuiteOut])
def list_suites(project: Project = Depends(owned_project), db: Session = Depends(get_db)):
    q = select(TestSuite).where(TestSuite.project_id == project.id).order_by(TestSuite.created_at)
    return db.scalars(q).all()


@router.post(
    "/projects/{project_id}/suites", response_model=SuiteOut, status_code=status.HTTP_201_CREATED
)
def create_suite(
    body: SuiteIn, project: Project = Depends(owned_project), db: Session = Depends(get_db)
):
    suite = TestSuite(project_id=project.id, **body.model_dump())
    db.add(suite)
    commit_or_409(db, "A suite with that name already exists in this project")
    return suite


@router.get("/suites/{suite_id}", response_model=SuiteOut)
def get_suite(suite: TestSuite = Depends(owned_suite)):
    return suite


@router.delete("/suites/{suite_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_suite(suite: TestSuite = Depends(owned_suite), db: Session = Depends(get_db)):
    db.delete(suite)
    db.commit()


# ---- cases ----
@router.get("/suites/{suite_id}/cases", response_model=list[CaseOut])
def list_cases(suite: TestSuite = Depends(owned_suite), db: Session = Depends(get_db)):
    q = (
        select(TestCase)
        .where(TestCase.suite_id == suite.id)
        .order_by(TestCase.created_at, TestCase.name)
    )
    return db.scalars(q).all()


@router.post(
    "/suites/{suite_id}/cases", response_model=CaseOut, status_code=status.HTTP_201_CREATED
)
def create_case(
    body: CaseIn, suite: TestSuite = Depends(owned_suite), db: Session = Depends(get_db)
):
    case = TestCase(suite_id=suite.id, **body.model_dump())
    db.add(case)
    db.commit()
    return case


@router.put("/cases/{case_id}", response_model=CaseOut)
def update_case(body: CaseIn, case: TestCase = Depends(owned_case), db: Session = Depends(get_db)):
    for key, value in body.model_dump().items():
        setattr(case, key, value)
    db.commit()
    return case


@router.delete("/cases/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_case(case: TestCase = Depends(owned_case), db: Session = Depends(get_db)):
    db.delete(case)
    db.commit()
