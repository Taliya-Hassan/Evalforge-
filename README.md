# EvalForge

Regression testing for LLM features: **define a suite → run it → read the diff.**
Full spec and architecture diagram: [docs/SPEC.md](docs/SPEC.md).

## Run everything locally (3 terminals)

**1. Database + API**
```bash
docker compose up -d db
cd backend
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env
alembic upgrade head
python -m scripts.seed_demo        # optional: demo@evalforge.dev / demo-password-123
uvicorn app.main:app --reload      # API docs: http://localhost:8000/docs
```

**2. Frontend**
```bash
cd frontend
npm install
npm run dev                        # http://localhost:5173
```

**Or** run DB + API only with Docker: `docker compose up --build`.

## Try it in 60 seconds (no API key needed)
1. Run the seed script, log in as the demo user.
2. Open *Support Bot → Smoke tests*. Two runs already exist (v1 and v2 of a "mock" model).
3. Click **Compare latest two runs**: you'll see 2 regressed, 1 improved, 3 unchanged cases.

To test a real model: add a model with provider `openai` or `anthropic`, set the key in `backend/.env`, and run.

## Checks (same as CI)
```bash
cd backend && ruff check . && pytest -q
cd frontend && npm run build
```

## How a run works
`POST /suites/{id}/runs` → run row created (`queued`) → background task loops over cases:
provider call → scorer → `results` row (errors are stored per case, never abort the run) → run `completed`.

## Project layout
```
backend/app/routers/   auth, projects(+models), suites(+cases), runs(+diff)
backend/app/services/  providers, scorers, runner, diff, stats
backend/alembic/       migrations
backend/tests/         auth, scorers, diff logic, end-to-end API flow
frontend/src/pages/    Login, Projects, ProjectDetail, SuiteDetail, RunView, DiffView
```

## Resetting the database
`docker compose down -v && docker compose up -d db && cd backend && alembic upgrade head`
