"""Creates a demo account with two mock model versions and two runs so the diff view has data.

Usage (from backend/):  python -m scripts.seed_demo
Login:  demo@evalforge.dev / demo-password-123
"""

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from app.db import SessionLocal, engine
from app.models import Model, Project, Run, TestCase, TestSuite, User
from app.security import hash_password
from app.services.runner import execute_run

EMAIL, PASSWORD = "demo@evalforge.dev", "demo-password-123"

CASES = [
    ("capital", "Capital of France?", "Paris", "contains"),
    ("math", "2+2?", "4", "exact_match"),
    ("translate", "Translate 'hello' to Spanish", "hola", "contains"),
    ("color", "Name a primary color", r"red|blue|yellow", "regex"),
    ("yesno", "Is the sky blue? Answer yes or no.", "yes", "exact_match"),
    ("planet", "Largest planet?", "Jupiter", "contains"),
]
V1 = {
    "Capital of France?": "The capital of France is Paris.",
    "2+2?": "4",
    "Translate 'hello' to Spanish": "Hola",
    "Name a primary color": "Red",
    "Is the sky blue? Answer yes or no.": "yes",
    "Largest planet?": "Saturn",
}
V2 = {
    **V1,
    "Capital of France?": "I believe it is Lyon.",
    "Is the sky blue? Answer yes or no.": "Yes, the sky is blue.",
    "Largest planet?": "Jupiter",
}


def main() -> None:
    with SessionLocal() as db:
        if db.scalar(select(User).where(User.email == EMAIL)):
            print("Demo data already exists.")
            return
        user = User(email=EMAIL, password_hash=hash_password(PASSWORD))
        db.add(user)
        db.flush()
        project = Project(owner_id=user.id, name="Support Bot", description="Demo project")
        db.add(project)
        db.flush()
        m1 = Model(project_id=project.id, name="v1 (baseline)", provider="mock",
                   model_identifier="mock-v1", params={"responses": V1})
        m2 = Model(project_id=project.id, name="v2 (new prompt)", provider="mock",
                   model_identifier="mock-v2", params={"responses": V2})
        suite = TestSuite(project_id=project.id, name="Smoke tests")
        db.add_all([m1, m2, suite])
        db.flush()
        for name, prompt, expected, scorer in CASES:
            db.add(TestCase(suite_id=suite.id, name=name, prompt=prompt,
                            expected_output=expected, scorer=scorer))
        db.flush()
        runs = [Run(suite_id=suite.id, model_id=m.id, triggered_by=user.id) for m in (m1, m2)]
        db.add_all(runs)
        db.commit()
        run_ids = [r.id for r in runs]
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    for rid in run_ids:
        execute_run(rid, factory)
    print(f"Seeded. Login with {EMAIL} / {PASSWORD}")


if __name__ == "__main__":
    main()
