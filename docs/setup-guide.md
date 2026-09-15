# Setup Guide — CourseGenie AI

> **This file is read by the automated evaluation pipeline. Be precise and complete.**

## Prerequisites

Before you begin, ensure you have the following installed:

- [ ] Python 3.11+
- [ ] Node.js 18+ (for the frontend)
- [ ] PostgreSQL 15+ — or Docker Desktop to run PostgreSQL in a container
- [ ] A Google account — get a free Gemini API key at <https://aistudio.google.com/app/apikey>

---

## Environment Variables

Copy `.env.example` to `.env` and fill in the values:

```bash
cp src/.env.example src/.env
```

Edit `src/.env` with the following:

| Variable | Description | Required |
|---|---|---|
| `GEMINI_API_KEY` | Google Gemini API key — get one free at <https://aistudio.google.com/app/apikey> | **Yes** |
| `GEMINI_MODEL` | Gemini model to use (default: `gemini-1.5-flash`) | No |
| `DATABASE_URL` | PostgreSQL connection string — `postgresql://<user>:<password>@<host>:<port>/<dbname>` | **Yes** |
| `SECRET_KEY` | JWT signing secret — generate with `python -c "import secrets; print(secrets.token_hex(32))"` | **Yes** |
| `APP_PORT` | Port the API server listens on (default `8000`) | No |
| `APP_ENV` | `development` or `production` — enables debug logging in development | No |
| `JWT_ALGORITHM` | JWT algorithm (default: `HS256`) | No |
| `JWT_EXPIRE_MINUTES` | Token lifetime in minutes (default: `10080` = 7 days) | No |

> **Note:** `DEEPSEEK_API_KEY` and `DEEPSEEK_MODEL` are also present in `.env.example` but are **not used at runtime** — DeepSeek is the legacy provider, preserved for easy restoration. The active provider is Google Gemini.

---

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-org/bob-ai-hackathon-TeachNexa.git
cd bob-ai-hackathon-TeachNexa

# 2. Create and activate a Python virtual environment
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS / Linux:
# source .venv/bin/activate

# 3. Install backend dependencies
pip install -r src/backend/requirements.txt
```

---

## Database Setup

### Option A — Docker (recommended for development)

```bash
docker run -d \
  --name coursegenie-db \
  -e POSTGRES_USER=coursegenie \
  -e POSTGRES_PASSWORD=changeme \
  -e POSTGRES_DB=coursegenie \
  -p 5432:5432 \
  postgres:15-alpine
```

### Option B — Local PostgreSQL

```bash
# Create the database and user (run inside psql as superuser)
psql -U postgres <<'SQL'
CREATE USER coursegenie WITH PASSWORD 'changeme';
CREATE DATABASE coursegenie OWNER coursegenie;
SQL
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

Three migration versions are included:
- `0001_initial.py` — creates all tables (users, courses, modules, topics, content, quizzes, questions)
- `0002_content_course_id.py` — adds `course_id` column to `content` table for revision anchoring
- `0003_add_password_hash.py` — adds `password_hash` column to `users` table for JWT auth

---

## Seed a Demo User (Optional)

The application seeds a demo user automatically on every startup via the FastAPI lifespan event (see [`app/seed.py`](../src/backend/app/seed.py)). The seed is idempotent — it is safe to run on every restart.

The demo user UUID is fixed at `00000000-0000-0000-0000-000000000001` with email `demo@coursegenie.ai`. This is used as a fallback owner for unauthenticated development scenarios.

To seed manually (if needed):

```bash
psql "$DATABASE_URL" -c "
INSERT INTO users (id, name, email, role)
VALUES (
  '00000000-0000-0000-0000-000000000001',
  'Demo User',
  'demo@coursegenie.ai',
  'instructor'
)
ON CONFLICT (id) DO NOTHING;"
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
Interactive Swagger docs: `http://localhost:8000/docs`  
ReDoc: `http://localhost:8000/redoc`

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

## First-Time User Flow

1. Open `http://localhost:3000`
2. Click **Sign Up** — create an account with your name, email, and password
3. You will be automatically logged in and redirected to the Dashboard
4. Click **Create Course** — paste any course syllabus text (minimum 20 characters)
5. Wait 5–30 seconds for AI generation (Google Gemini API latency)
6. Browse the generated course — click any topic to generate learning content or a quiz

---

## Running Tests

Tests use an **in-memory SQLite** database — no live PostgreSQL required.

```bash
# Run all tests with verbose output (from repository root)
pytest -v

# Run a single test file
pytest src/backend/tests/test_generate_endpoint.py -v

# Run with coverage (if pytest-cov is installed)
pytest --cov=src/backend/app -v
```

Expected: all 11 test files pass.

Test files and what they cover:

| File | Coverage |
|---|---|
| `test_auth.py` | Signup, login, `/me`, duplicate email, wrong password |
| `test_courses.py` | `GET /api/courses`, `GET /api/courses/{id}`, ownership enforcement |
| `test_database.py` | ORM model creation, CRUD, relationships, constraint enforcement |
| `test_demo_ownership.py` | Demo user seed + ownership validation |
| `test_edit.py` | `PATCH` for course, module, topic — valid + invalid cases |
| `test_file_upload_flow.py` | File-based syllabus input edge cases |
| `test_generate_endpoint.py` | `POST /api/v1/courses/generate` — AI mock + real structure validation |
| `test_health.py` | `GET /health` response shape and status |
| `test_syllabus.py` | `POST /api/v1/syllabus` — validation, edge cases |
| `test_topics.py` | Topic content, quiz, revision generation + retrieval; idempotent replacement |

---

## Project Structure (Backend)

```
src/
  backend/
    app/
      api/
        health.py           ← GET /health
        syllabus.py         ← POST /api/v1/syllabus
      routers/
        auth.py             ← POST /api/auth/signup|login, GET /api/auth/me
        courses.py          ← GET/PATCH /api/courses, POST /api/v1/courses/generate
        topics.py           ← POST/GET content, quiz, revision; PATCH module/topic
      services/
        auth_service.py     ← JWT create/verify (python-jose), bcrypt hash/verify
        deepseek_client.py  ← Google Gemini AI wrapper (4 generation methods)
        syllabus_service.py ← Syllabus processing logic
      schemas/
        auth.py             ← SignupRequest, LoginRequest, AuthResponse, UserOut
        courses.py          ← CourseListItem, CourseDetail, CoursesListResponse
        generate.py         ← GenerateCourseRequest, GenerateCourseResponse
        topics.py           ← TopicContentResponse, QuizResponse, RevisionResponse
      config.py             ← Settings (pydantic-settings; reads .env)
      main.py               ← FastAPI app + lifespan seed + router registration
      seed.py               ← Demo user idempotent seed
    database/
      connection.py         ← SQLAlchemy engine + Base + verify_connection()
      models.py             ← ORM: User, Course, Module, Topic, Content, Quiz, Question
      session.py            ← SessionLocal factory + get_db() FastAPI dependency
    migrations/
      env.py                ← Alembic environment (reads DATABASE_URL)
      versions/
        0001_initial.py     ← initial schema (all tables)
        0002_content_course_id.py  ← course_id on content table
        0003_add_password_hash.py  ← password_hash on users table
    tests/
      conftest.py                ← pytest fixtures (in-memory SQLite + scoped sessions)
      test_auth.py               ← auth flow tests
      test_courses.py            ← course CRUD + ownership
      test_database.py           ← model + constraint tests
      test_demo_ownership.py     ← demo user + ownership
      test_edit.py               ← PATCH endpoint tests
      test_file_upload_flow.py   ← file upload edge cases
      test_generate_endpoint.py  ← AI generation endpoint
      test_health.py             ← health check
      test_syllabus.py           ← syllabus endpoint
      test_topics.py             ← topic content/quiz/revision
    requirements.txt        ← Python dependencies
    alembic.ini             ← Alembic configuration
  frontend/
    src/
      pages/
        AuthPage.jsx                ← Login + Signup
        Dashboard.jsx               ← Course grid
        CreateCourse.jsx            ← Syllabus input + generation progress
        CourseOverview.jsx          ← Module/topic tree
        TopicLearning.jsx           ← Per-topic content display
        QuizPage.jsx                ← MCQ quiz with score screen
        RevisionCenter.jsx          ← Revision notes + question bank
      services/api/
        syllabusService.js          ← generateCourse() → POST /api/v1/courses/generate
        courseService.js            ← getCourses(), getCourse()
        topicService.js             ← generateTopicContent(), getTopicContent()
        quizService.js              ← generateQuiz(), getQuiz(), generateRevision(), getRevision()
      store/
        useGenerationStore.js       ← Zustand store for generation lifecycle
```

---

## Troubleshooting

| Issue | Solution |
|---|---|
| `ModuleNotFoundError: No module named 'backend'` | Run pytest/uvicorn from the repo root with `src` on the Python path, or activate the venv |
| `connection refused` on port 5432 | Ensure PostgreSQL is running: `docker start coursegenie-db` |
| `FATAL: password authentication failed` | Check `DATABASE_URL` in `src/.env` matches the DB user/password |
| `alembic: command not found` | Run `pip install alembic` or activate your virtual environment |
| `target database is not up to date` | Run `alembic -c src/backend/alembic.ini upgrade head` |
| Gemini `401 / AuthenticationError` | Check `GEMINI_API_KEY` in `src/.env` — get a key at <https://aistudio.google.com/app/apikey> |
| Gemini `429 / RateLimitError` | Free tier has rate limits — wait a few seconds and retry, or upgrade your Gemini plan |
| `IntegrityError: UNIQUE constraint failed` | Normal for re-generation — old content rows are deleted before inserting. If it persists, check the migration has run: `alembic current` |
| JWT `401 Unauthorized` on all routes | Token expired or `SECRET_KEY` changed — log in again via `POST /api/auth/login` |
| Frontend shows "Network Error" | Ensure the backend is running on port 8000 and CORS is configured (`APP_ENV=development`) |
| `npm: command not found` | Install Node.js 18+ from <https://nodejs.org> |
