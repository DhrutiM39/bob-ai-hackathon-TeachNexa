# Setup Guide

> **This file is read by the automated evaluation pipeline. Be precise and complete.**

## Prerequisites

Before you begin, ensure you have the following installed:

- [ ] Python 3.11+
- [ ] PostgreSQL 15+ (or Docker Desktop to run PostgreSQL in a container)
- [ ] An IBM Cloud account with watsonx.ai access

---

## Environment Variables

Copy `.env.example` to `.env` and fill in the values:

```bash
cp src/.env.example src/.env
```

| Variable | Description | Required |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string — `postgresql://<user>:<password>@<host>:<port>/<dbname>` | Yes |
| `WATSONX_API_KEY` | IBM watsonx.ai API key | Yes |
| `WATSONX_PROJECT_ID` | watsonx.ai project ID | Yes |
| `WATSONX_URL` | watsonx.ai regional endpoint | Yes |
| `APP_PORT` | Port the API server listens on (default `8000`) | No |
| `APP_ENV` | `development` or `production` — enables SQL echo in development | No |
| `SLACK_WEBHOOK_URL` | Slack webhook for notifications | No |

---

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-org/bob-ai-hackathon-TeachNexa.git
cd bob-ai-hackathon-TeachNexa

# 2. Create and activate a Python virtual environment
python -m venv .venv
# macOS/Linux:
source .venv/bin/activate
# Windows PowerShell:
.venv\Scripts\Activate.ps1

# 3. Install backend dependencies
pip install -r src/backend/requirements.txt
```

---

## Database Setup

### Option A — Local PostgreSQL

```bash
# Create the database and user (run inside psql as superuser)
psql -U postgres <<'SQL'
CREATE USER coursegenie WITH PASSWORD 'changeme';
CREATE DATABASE coursegenie OWNER coursegenie;
SQL
```

### Option B — Docker (recommended for development)

```bash
docker run -d \
  --name coursegenie-db \
  -e POSTGRES_USER=coursegenie \
  -e POSTGRES_PASSWORD=changeme \
  -e POSTGRES_DB=coursegenie \
  -p 5432:5432 \
  postgres:15-alpine
```

---

## Running Migrations

Migrations are managed with **Alembic**. Always run from the repository root.

```bash
# Apply all pending migrations (creates all tables)
alembic -c src/backend/alembic.ini upgrade head

# Check current migration version
alembic -c src/backend/alembic.ini current

# Roll back the most recent migration
alembic -c src/backend/alembic.ini downgrade -1

# Auto-generate a new migration after changing models.py
alembic -c src/backend/alembic.ini revision --autogenerate -m "describe your change"
```

> **Note:** `alembic.ini` stores a fallback `sqlalchemy.url`. At runtime,
> `env.py` overrides this with the value of the `DATABASE_URL` environment
> variable, so only the `.env` value matters in practice.

---

## Verifying the Database Connection

```bash
# Quick Python check — prints True if connection succeeds
python - <<'PY'
import os, sys
sys.path.insert(0, "src")
os.environ.setdefault("DATABASE_URL", "postgresql://coursegenie:changeme@localhost:5432/coursegenie")
from backend.database.connection import verify_connection
print("Connection OK:", verify_connection())
PY
```

---

## Running the Application

```bash
# Start the FastAPI backend (from repository root)
uvicorn backend.main:app --reload --port 8000 --app-dir src
```

The API will be available at: `http://localhost:8000`  
Interactive docs: `http://localhost:8000/docs`

---

## Running Tests

Tests use an **in-memory SQLite** database — no live PostgreSQL required.

```bash
# Run all database tests
pytest

# With coverage
pytest --cov=src/backend/database
```

---

## Project Structure (Database Layer)

```
src/
  backend/
    database/
      __init__.py      ← public API (engine, Base, get_db, models)
      connection.py    ← SQLAlchemy engine + Base + verify_connection()
      models.py        ← ORM models: User, Course, Module, Topic, Content, Quiz, Question
      session.py       ← SessionLocal factory + get_db() FastAPI dependency
    migrations/
      env.py           ← Alembic environment (reads DATABASE_URL)
      script.py.mako   ← migration file template
      versions/
        0001_initial.py ← initial schema migration
    tests/
      conftest.py      ← pytest fixtures (in-memory SQLite engine + scoped sessions)
      test_database.py ← model creation, CRUD, relationship, constraint tests
    requirements.txt   ← Python dependencies
    alembic.ini        ← Alembic configuration
```

---

## Troubleshooting

| Issue | Solution |
|---|---|
| `ModuleNotFoundError: No module named 'backend'` | Ensure you run pytest/uvicorn from the repo root with `src` on the Python path, or activate the venv. |
| `connection refused` on port 5432 | Ensure PostgreSQL is running: `docker start coursegenie-db` |
| `FATAL: password authentication failed` | Check `DATABASE_URL` in your `.env` matches the DB user/password |
| `alembic: command not found` | Run `pip install alembic` or activate your virtual environment |
| `target database is not up to date` | Run `alembic -c src/backend/alembic.ini upgrade head` |
| watsonx.ai 401 error | Check `WATSONX_API_KEY` in your `.env` file |
