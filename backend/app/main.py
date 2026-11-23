from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth, projects, runs, suites

app = FastAPI(title="EvalForge", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)
for r in (auth.router, projects.router, suites.router, runs.router):
    app.include_router(r)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
