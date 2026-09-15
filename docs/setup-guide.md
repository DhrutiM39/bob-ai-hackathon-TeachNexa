# Setup Guide

> **This file is read by the automated evaluation pipeline. Be precise and complete.**

## Prerequisites

Before you begin, ensure you have the following installed:

- [ ] Python 3.11+
- [ ] Node.js 18+ (for the frontend)
- [ ] PostgreSQL 15+ (or Docker Desktop to run PostgreSQL in a container)
- [ ] A DeepSeek account — get a free API key at <https://platform.deepseek.com/api_keys>

---

## Environment Variables

Copy `.env.example` to `.env` and fill in the values:

```bash
cp src/.env.example src/.env
```

| Variable | Description | Required |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string — `postgresql://<user>:<password>@<host>:<port>/<dbname>` | Yes |
| `DEEPSEEK_API_KEY` | DeepSeek API key — get one at <https://platform.deepseek.com/api_keys> | Yes |
| `DEEPSEEK_MODEL` | Model to use (default: `deepseek-chat`) | No |
| `APP_PORT` | Port the API server listens on (default `8000`) | No |
| `APP_ENV` | `development` or `production` — enables SQL echo in development | No |
| `VITE_DEMO_OWNER_ID` | UUID of the demo user seeded in the DB (see "Seed a demo user" below) | No |

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

## Seed a demo user

Until authentication is implemented, the frontend uses a fixed `DEMO_OWNER_ID`
as the `owner_id` FK when calling `POST /api/v1/courses/generate`.
Insert a matching row **once** after running migrations:

```sql
-- Run with: psql $DATABASE_URL
INSERT INTO users (id, name, email, role)
VALUES (
  '00000000-0000-0000-0000-000000000001',
  'Demo User',
  'demo@coursegenie.ai',
  'instructor'
)
ON CONFLICT (id) DO NOTHING;
```

Or as a one-liner from the shell:

```bash
psql "$DATABASE_URL" -c "INSERT INTO users (id, name, email, role) VALUES ('00000000-0000-0000-0000-000000000001', 'Demo User', 'demo@coursegenie.ai', 'instructor') ON CONFLICT (id) DO NOTHING;"
```

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

### Backend

```bash
# Start the FastAPI backend (from repository root)
uvicorn backend.app.main:app --reload --port 8000 --app-dir src
```

The API will be available at: `http://localhost:8000`
Interactive docs: `http://localhost:8000/docs`

### Frontend

```bash
# In a separate terminal, from the repository root:
cd src/frontend
npm install          # first time only
npm run dev
```

The frontend will be available at: `http://localhost:3000`

> **Tip:** The Vite dev server proxies `/api/*` requests to `http://localhost:8000`
> by default (see `vite.config.js`). No `VITE_API_BASE_URL` is needed in dev.

---

## Running Tests

Tests use an **in-memory SQLite** database — no live PostgreSQL required.

```bash
# Run all tests with verbose output (from repository root)
pytest -v

# Run a single test file
pytest src/backend/tests/test_generate_endpoint.py -v
```

Expected output: all six test files pass — `test_database`, `test_generate_endpoint`,
`test_health`, `test_syllabus`, `test_courses`, and `test_topics`.

---

## Project Structure (Backend)

```
src/
  backend/
    app/
      api/
        health.py       ← GET /health
        syllabus.py     ← POST /api/v1/syllabus
      routers/
        courses.py      ← GET /api/courses, GET /api/courses/{id}, POST /api/v1/courses/generate
        topics.py       ← POST/GET /api/topics/{id}/generate-content, /content
                           POST/GET /api/topics/{id}/generate-quiz, /quiz
                           POST/GET /api/courses/{id}/generate-revision, /revision
      services/
        deepseek_client.py  ← DeepSeek AI wrapper (OpenAI-compatible)
                               generate_course_structure(), generate_topic_content(),
                               generate_quiz(), generate_revision()
        syllabus_service.py ← Syllabus processing logic
      schemas/
        courses.py      ← CourseListItem, CourseDetail, CoursesListResponse
        generate.py     ← GenerateCourseRequest, GenerateCourseResponse
        topics.py       ← TopicContentResponse, QuizResponse, RevisionResponse
      config.py         ← Settings (pydantic-settings; reads .env)
      main.py           ← FastAPI app + router registration
      seed.py           ← Demo user seed script
    database/
      connection.py     ← SQLAlchemy engine + Base + verify_connection()
      models.py         ← ORM models: User, Course, Module, Topic, Content, Quiz, Question
      session.py        ← SessionLocal factory + get_db() FastAPI dependency
    migrations/
      env.py            ← Alembic environment (reads DATABASE_URL)
      versions/
        0001_initial.py ← initial schema migration
    tests/
      conftest.py                ← pytest fixtures (in-memory SQLite + scoped sessions)
      test_database.py           ← model creation, CRUD, relationship, constraint tests
      test_generate_endpoint.py  ← DeepSeekClient unit + endpoint integration tests
      test_health.py             ← GET /health tests
      test_syllabus.py           ← POST /api/v1/syllabus tests
      test_courses.py            ← GET /api/courses, GET /api/courses/{id}, POST generate tests
      test_topics.py             ← topic content, quiz, revision endpoint tests
    requirements.txt    ← Python dependencies
    alembic.ini         ← Alembic configuration
  frontend/
    src/
      pages/CreateCourse.jsx          ← Course creation form + generation progress
      pages/TopicLearning.jsx         ← Per-topic content display
      pages/QuizPage.jsx              ← MCQ quiz with score screen
      pages/RevisionCenter.jsx        ← Revision notes + question bank
      services/api/syllabusService.js ← generateCourse() → POST /api/v1/courses/generate
      services/api/courseService.js   ← getCourses(), getCourse()
      services/api/topicService.js    ← generateTopicContent(), getTopicContent()
      services/api/quizService.js     ← generateQuiz(), getQuiz(), generateRevision(), getRevision()
      store/useGenerationStore.js     ← Zustand store for generation lifecycle
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
| DeepSeek 401 / AuthenticationError | Check `DEEPSEEK_API_KEY` in your `.env` file — get a key at <https://platform.deepseek.com/api_keys> |
| `IntegrityError` on course generate — FK violation on `owner_id` | Run the "Seed a demo user" SQL snippet above |
