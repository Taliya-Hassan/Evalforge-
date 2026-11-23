from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import commit_or_409, get_current_user, owned_model, owned_project
from app.models import Model, Project, User
from app.schemas import ModelIn, ModelOut, ProjectIn, ProjectOut

router = APIRouter(tags=["projects"])


@router.get("/projects", response_model=list[ProjectOut])
def list_projects(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = select(Project).where(Project.owner_id == user.id).order_by(Project.created_at.desc())
    return db.scalars(q).all()


@router.post("/projects", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    body: ProjectIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    project = Project(owner_id=user.id, **body.model_dump())
    db.add(project)
    commit_or_409(db, "You already have a project with that name")
    return project


@router.get("/projects/{project_id}", response_model=ProjectOut)
def get_project(project: Project = Depends(owned_project)):
    return project


@router.put("/projects/{project_id}", response_model=ProjectOut)
def update_project(
    body: ProjectIn, project: Project = Depends(owned_project), db: Session = Depends(get_db)
):
    project.name, project.description = body.name, body.description
    commit_or_409(db, "You already have a project with that name")
    return project


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project: Project = Depends(owned_project), db: Session = Depends(get_db)):
    db.delete(project)
    db.commit()


# ---- models under a project ----
@router.get("/projects/{project_id}/models", response_model=list[ModelOut])
def list_models(project: Project = Depends(owned_project), db: Session = Depends(get_db)):
    q = select(Model).where(Model.project_id == project.id).order_by(Model.created_at)
    return db.scalars(q).all()


@router.post(
    "/projects/{project_id}/models", response_model=ModelOut, status_code=status.HTTP_201_CREATED
)
def create_model(
    body: ModelIn, project: Project = Depends(owned_project), db: Session = Depends(get_db)
):
    model = Model(project_id=project.id, **body.model_dump())
    db.add(model)
    db.commit()
    return model


@router.delete("/models/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_model(model: Model = Depends(owned_model), db: Session = Depends(get_db)):
    db.delete(model)
    commit_or_409(db, "This model has runs and cannot be deleted")
