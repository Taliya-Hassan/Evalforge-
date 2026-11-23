import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Model, Project, Run, TestCase, TestSuite, User
from app.security import decode_access_token

bearer = HTTPBearer(auto_error=False)


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    unauthorized = HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        "Invalid or missing token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if creds is None:
        raise unauthorized
    sub = decode_access_token(creds.credentials)
    if sub is None:
        raise unauthorized
    try:
        user = db.get(User, uuid.UUID(sub))
    except ValueError:
        raise unauthorized from None
    if user is None:
        raise unauthorized
    return user


def commit_or_409(db: Session, message: str) -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, message) from None


def _project_or_404(db: Session, user: User, project_id: uuid.UUID, what: str) -> Project:
    project = db.get(Project, project_id)
    if project is None or project.owner_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"{what} not found")
    return project


# Ownership is always checked through the project, and a foreign id looks like "not found".
def owned_project(
    project_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Project:
    return _project_or_404(db, user, project_id, "Project")


def owned_model(
    model_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Model:
    model = db.get(Model, model_id)
    if model is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Model not found")
    _project_or_404(db, user, model.project_id, "Model")
    return model


def owned_suite(
    suite_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TestSuite:
    suite = db.get(TestSuite, suite_id)
    if suite is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Suite not found")
    _project_or_404(db, user, suite.project_id, "Suite")
    return suite


def owned_case(
    case_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TestCase:
    case = db.get(TestCase, case_id)
    if case is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Test case not found")
    suite = db.get(TestSuite, case.suite_id)
    _project_or_404(db, user, suite.project_id, "Test case")
    return case


def owned_run(
    run_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Run:
    run = db.get(Run, run_id)
    if run is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Run not found")
    suite = db.get(TestSuite, run.suite_id)
    _project_or_404(db, user, suite.project_id, "Run")
    return run
