# Developer Guide — CourseGenie AI

This guide covers how the project is structured, how to extend it, and key conventions used throughout the codebase.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Repository Layout](#2-repository-layout)
3. [Backend Conventions](#3-backend-conventions)
4. [Frontend Conventions](#4-frontend-conventions)
5. [AI Integration](#5-ai-integration)
6. [Database & Migrations](#6-database--migrations)
7. [Authentication](#7-authentication)
8. [Testing Strategy](#8-testing-strategy)
9. [Environment Variables Reference](#9-environment-variables-reference)
10. [How to Add a New Feature](#10-how-to-add-a-new-feature)

---

## 1. Project Overview

CourseGenie AI transforms a plain course syllabus into a complete learning experience using Google Gemini AI. The system is split into:

- **FastAPI backend** (`src/backend/`) — REST API, AI generation, database persistence
- **React 18 frontend** (`src/frontend/`) — SPA with JWT auth, TanStack Query, Zustand

The backend is the source of truth for all data. The frontend is a thin display layer that calls REST endpoints and caches responses.

---

## 2. Repository Layout

```
bob-ai-hackathon-TeachNexa/
├── src/
│   ├── .env.example          ← copy to .env; never commit .env
│   ├── backend/              ← Python FastAPI application
│   └── frontend/             ← React 18 SPA
├── docs/
│   ├── problem-statement.md  ← problem context
│   ├── solution-overview.md  ← how the solution works
│   ├── architecture.md       ← system architecture + Mermaid diagram
│   ├── setup-guide.md        ← step-by-step run instructions
│   └── template-guide.md     ← this file — developer guide
├── demo/                     ← screenshots, video link, live demo URL
├── presentation/             ← slide deck
├── submission.yaml           ← structured hackathon submission metadata
└── README.md                 ← project overview
```

---

## 3. Backend Conventions

### Module layout

```
src/backend/
  app/
    api/         ← thin routers for simple endpoints (health, syllabus)
    routers/     ← feature routers (auth, courses, topics)
    schemas/     ← Pydantic request/response models only — no logic
    services/    ← all business logic, AI calls, password/JWT ops
    config.py    ← pydantic-settings singleton
    main.py      ← FastAPI app + lifespan + router registration
    seed.py      ← idempotent demo user seed
  database/
    connection.py  ← engine + Base
    models.py      ← SQLAlchemy ORM models
    session.py     ← get_db() FastAPI dependency
  migrations/    ← Alembic migration versions
  tests/         ← all pytest tests
```

### Route handler pattern

Route handlers must be **thin** — they validate, call a service or helper, and return:

```python
@router.post("/api/topics/{topic_id}/generate-content", ...)
def generate_topic_content(
    topic_id: str,
    db: Session = Depends(get_db),
    ds: DeepSeekClient = Depends(get_deepseek_client),
    current_user: User = Depends(get_current_user),
) -> TopicContentResponse:
    topic = _get_topic_or_404(db, topic_id)          # validate
    course = _assert_topic_owner(db, topic, current_user)  # authorise
    content_data, model = ds.generate_topic_content(...)   # AI call
    # ... persist
    return _content_to_response(content_row, topic.id)     # return
```

No SQL inside route handlers. All DB access goes through helper functions in the same file.

### Ownership enforcement

Every mutating endpoint resolves `owner_id` from the JWT — never from the request body. The pattern is:

```python
current_user: User = Depends(get_current_user)   # always injected
# then:
if course.owner_id != current_user.id:
    raise HTTPException(status_code=403, ...)
```

### Error codes

| Scenario | HTTP Code |
|---|---|
| Invalid UUID | 400 |
| Not found | 404 |
| Wrong owner | 403 |
| Duplicate (e.g. email) | 409 |
| AI response malformed | 422 |
| AI API unreachable | 502 |
| Pydantic validation | 422 (FastAPI built-in) |

---

## 4. Frontend Conventions

### State management split

| Layer | Tool | What it manages |
|---|---|---|
| Server state | TanStack Query v5 | All backend data (courses, content, quizzes) |
| UI/local state | Zustand | Auth token + user, generation flow progress |
| Component state | React `useState` | Form inputs, toggles, accordion open/close |

Never put server data in Zustand. Never put ephemeral UI state in TanStack Query.

### Query key conventions

Query keys always include the resource type and relevant IDs:

```js
['courses']                    // list
['courses', courseId]          // single course
['topics', topicId, 'content'] // topic content
['topics', topicId, 'quiz']    // topic quiz
['courses', courseId, 'revision']  // revision
```

### API service layer

All HTTP calls go through `src/frontend/src/services/api/`:

- `syllabusService.js` → `generateCourse()`
- `courseService.js` → `getCourses()`, `getCourse()`
- `topicService.js` → `generateTopicContent()`, `getTopicContent()`
- `quizService.js` → `generateQuiz()`, `getQuiz()`, `generateRevision()`, `getRevision()`

Each function returns the raw Axios response data. Adapter functions in `services/adapters/` normalise field names defensively before passing data to components.

### Auth

JWT is stored in Zustand + `localStorage`. The Axios instance attaches it via a request interceptor. On 401 response, the store clears the token and redirects to `/login`.

---

## 5. AI Integration

The `DeepSeekClient` class in [`services/deepseek_client.py`](../src/backend/app/services/deepseek_client.py) is the single point of contact with the AI provider.

**Active provider:** Google Gemini (`gemini-1.5-flash`) via `https://generativelanguage.googleapis.com/v1beta/openai/`

**To switch providers (e.g. back to DeepSeek):**

1. Change `_get_client()` to use `base_url="https://api.deepseek.com"` and `api_key=self._settings.deepseek_api_key`
2. Change the `model` variable references from `self._settings.gemini_model` to `self._settings.deepseek_model`
3. Set `DEEPSEEK_API_KEY` in `.env`

**Prompt engineering rules:**
- All prompts end with `Return ONLY a valid JSON object — no markdown, no explanation, no code fences.`
- `_extract_json()` strips fences in case the model ignores the instruction
- Temperature is kept low (0.2–0.3) for structured JSON output
- `max_tokens` is set conservatively per method (2048–3500)

**Adding a new generation method:**
1. Write a `_NEW_PROMPT` template string at module level
2. Add a method `generate_X(self, ...)` following the same pattern as existing methods
3. Add a route handler in the appropriate router
4. Add a test with a mocked `DeepSeekClient`

---

## 6. Database & Migrations

### ORM model conventions

- All primary keys are `Uuid` type (PostgreSQL native UUID; maps to Python `uuid.UUID`)
- `created_at` defaults to `datetime.now(timezone.utc)` via `_now()`
- Cascade deletes propagate from parent to children (Course → Modules → Topics → Content/Quizzes)
- Unique constraints on `(topic_id, content_type)` and `(course_id, content_type)` enforce at-most-one-item-per-parent

### Creating a migration

```bash
# After modifying models.py:
alembic -c src/backend/alembic.ini revision --autogenerate -m "describe change"

# Review the generated file in migrations/versions/ before applying
alembic -c src/backend/alembic.ini upgrade head
```

### PostgreSQL vs SQLite differences

| Concern | PostgreSQL | SQLite (tests) |
|---|---|---|
| `options` column | `JSONB` | `JSON` (plain) |
| UUID type | native `UUID` | stored as `VARCHAR(36)` |
| Unique index on NULLs | NULL ≠ NULL (compliant) | NULL ≠ NULL (compliant) |

The Alembic `env.py` detects the dialect and uses `JSONB` only on PostgreSQL.

---

## 7. Authentication

### Flow

```
POST /api/auth/signup
  Body: { name, email, password }
  → bcrypt.hashpw(password) → stored as password_hash
  → create_access_token(user.id) → HS256 JWT
  ← { access_token, user_id, name, email, role }

POST /api/auth/login
  Body: { email, password }
  → load user by email
  → bcrypt.checkpw(password, password_hash)  ← constant-time
  → create_access_token(user.id)
  ← { access_token, ... }

All protected routes:
  Header: Authorization: Bearer <token>
  → get_current_user() decodes JWT → loads User from DB
  → raises 401 if token missing/invalid/expired
```

### Changing token expiry

Set `JWT_EXPIRE_MINUTES` in `.env` (default: 10080 = 7 days).

### Rotating the secret

Change `SECRET_KEY` in `.env` and restart. All existing tokens immediately become invalid — users must log in again.

---

## 8. Testing Strategy

All tests are in `src/backend/tests/`. The test suite uses:

- **pytest** as runner
- **httpx** via FastAPI `TestClient` for endpoint tests
- **In-memory SQLite** via a scoped `SessionLocal` fixture in `conftest.py` — no PostgreSQL required
- **`unittest.mock.MagicMock`** for the `DeepSeekClient` — no Gemini API calls in CI

### Running tests

```bash
pytest -v                                         # all tests
pytest src/backend/tests/test_auth.py -v          # single file
pytest -k "test_generate" -v                      # by name pattern
pytest --tb=short -v                              # short tracebacks
```

### Writing a new test

```python
def test_my_new_endpoint(client, db_session):
    # client: FastAPI TestClient (from conftest.py)
    # db_session: in-memory SQLite session
    response = client.post("/api/my-route", json={...}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 201
    assert response.json()["field"] == "expected"
```

---

## 9. Environment Variables Reference

| Variable | Default | Used by | Notes |
|---|---|---|---|
| `GEMINI_API_KEY` | `""` | `DeepSeekClient` | Required for AI generation |
| `GEMINI_MODEL` | `gemini-1.5-flash` | `DeepSeekClient` | Override to use a different model |
| `DEEPSEEK_API_KEY` | `""` | Legacy | Not used at runtime |
| `DEEPSEEK_MODEL` | `deepseek-chat` | Legacy | Not used at runtime |
| `DATABASE_URL` | `postgresql://coursegenie:changeme@localhost:5432/coursegenie` | SQLAlchemy | Must point to a running PG instance |
| `SECRET_KEY` | `change-me-...` | `auth_service` | Must be set to a random value in any real deployment |
| `JWT_ALGORITHM` | `HS256` | `auth_service` | No reason to change |
| `JWT_EXPIRE_MINUTES` | `10080` | `auth_service` | 7 days |
| `APP_ENV` | `development` | `main.py` | `development` → DEBUG logs + open CORS |
| `APP_PORT` | `8000` | Uvicorn (informational) | Pass `--port` to Uvicorn separately |
| `VITE_API_BASE_URL` | _(empty)_ | Vite proxy | Empty = same origin (dev proxy handles it) |
| `VITE_USE_MOCKS` | `false` | Frontend | `true` → serve fixture data, no backend needed |

---

## 10. How to Add a New Feature

### Example: add a new AI generation endpoint (e.g. "generate glossary")

**1. Add a prompt template** in [`deepseek_client.py`](../src/backend/app/services/deepseek_client.py):
```python
_GLOSSARY_PROMPT = """..."""
```

**2. Add a method** to `DeepSeekClient`:
```python
def generate_glossary(self, topic_title: str, ...) -> tuple[dict, str]:
    ...
```

**3. Add a Pydantic schema** in `src/backend/app/schemas/`:
```python
class GlossaryResponse(BaseModel):
    topic_id: uuid.UUID
    terms: list[GlossaryTerm]
    generated_at: datetime
```

**4. Add a route handler** in `src/backend/app/routers/topics.py`:
```python
@router.post("/api/topics/{topic_id}/generate-glossary", response_model=GlossaryResponse, ...)
def generate_topic_glossary(topic_id: str, db=Depends(get_db), ds=Depends(get_deepseek_client), current_user=Depends(get_current_user)):
    ...
```

**5. Add a migration** if new DB columns are needed:
```bash
alembic -c src/backend/alembic.ini revision --autogenerate -m "add glossary to content"
alembic -c src/backend/alembic.ini upgrade head
```

**6. Add a test** in `src/backend/tests/test_topics.py` with a mocked `DeepSeekClient`.

**7. Add a frontend service function** in `src/frontend/src/services/api/topicService.js` and a TanStack Query hook.

**8. Add the UI** in `src/frontend/src/pages/TopicLearning.jsx` or a new page.
