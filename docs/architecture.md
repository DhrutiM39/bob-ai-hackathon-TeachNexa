# Architecture — CourseGenie AI

## Overview

CourseGenie AI is an AI Professor Assistant that transforms a plain college syllabus into a complete, structured course — modules, topics, learning content, quizzes, and revision materials — powered by **Google Gemini AI** (`gemini-1.5-flash`) via its OpenAI-compatible API.

---

## System Architecture

```mermaid
graph TD
    subgraph Browser
        A[Professor / User]
        B["React 18 Frontend\n(Vite 5 · React Router v6\nTanStack Query v5 · Zustand\nAxios · CSS Modules)"]
    end

    subgraph "FastAPI Backend  :8000"
        C["main.py\nFastAPI app\n+ CORS + Lifespan seed"]
        D["GET /health\nLiveness check"]
        E["POST /api/v1/syllabus\nSyllabus ingest & validation"]
        AUTH["Auth router\nPOST /api/auth/signup\nPOST /api/auth/login\nGET  /api/auth/me"]
        F["Courses router\nGET  /api/courses\nGET  /api/courses/:id\nPOST /api/v1/courses/generate\nPATCH /api/courses/:id"]
        G["Topics router\nPOST /api/topics/:id/generate-content\nGET  /api/topics/:id/content\nPOST /api/topics/:id/generate-quiz\nGET  /api/topics/:id/quiz\nPOST /api/courses/:id/generate-revision\nGET  /api/courses/:id/revision\nPATCH /api/modules/:id\nPATCH /api/topics/:id"]
        H["AuthService\nbcrypt hash/verify\nJWT create/verify"]
        I["pydantic-settings\nConfig · .env loader"]
    end

    subgraph "Google Gemini AI"
        J["DeepSeekClient\nopenai SDK (OpenAI-compatible)\ngenerate_course_structure()\ngenerate_topic_content()\ngenerate_quiz()\ngenerate_revision()"]
        K["gemini-1.5-flash model\n(Google Generative Language API)"]
    end

    subgraph "Data Layer"
        L["SQLAlchemy 2.0 ORM\nSession · Engine"]
        M[("PostgreSQL 15\ncoursegenie DB")]
        N["Alembic\nmigrations (0001–0003)"]
    end

    A -->|"HTTPS · JSON"| B
    B -->|"REST / Axios\nJWT Bearer token"| C
    C --> D
    C --> E
    C --> AUTH
    C --> F
    C --> G
    AUTH --> H
    H --> I
    F --> L
    G --> L
    F -->|"generate course structure"| J
    G -->|"generate content\ngenerate quiz\ngenerate revision"| J
    J --> K
    K -->|"structured JSON\nresponse"| J
    J -->|"parsed result"| F
    J -->|"parsed result"| G
    L --> M
    N -.->|"schema migrations"| M
```

---

## Layer-by-Layer Breakdown

### Frontend — `src/frontend/`

| Concern | Detail |
|---|---|
| Framework | React 18 + Vite 5 |
| Routing | React Router v6 — 6 routes, all lazy-loaded via `React.lazy/Suspense` |
| Server state | TanStack Query v5 — `useCourses`, `useTopicContent`, `useQuiz`, `useRevision` hooks; 5-minute stale time |
| UI state | Zustand — isolated to auth store and syllabus-generation flow store (`useGenerationStore`) |
| Styling | CSS Modules + centralised design tokens (`src/styles/tokens.css`) |
| HTTP client | Axios — base URL read from `VITE_API_BASE_URL` env var; JWT attached via request interceptor |
| Adapters | `services/adapters/` — normalise backend field names defensively (snake_case / camelCase / fallbacks) |
| Mocks | `VITE_USE_MOCKS=true` serves fixture data from `mocks/mockData.js` — clearly labelled in UI |

**Routes served:**

| URL | Page | Description |
|---|---|---|
| `/` | Dashboard | Course grid, empty state, link to create |
| `/login` | Login | Email + password → JWT |
| `/signup` | Sign Up | Name + email + password → JWT |
| `/create` | Create Course | Syllabus input + named-stage AI generation progress |
| `/courses/:courseId` | Course Overview | Expandable module/topic tree |
| `/courses/:courseId/topics/:topicId` | Topic Learning | Content + sidebar |
| `/courses/:courseId/topics/:topicId/quiz` | Quiz | MCQ, navigation, score screen |
| `/courses/:courseId/revision` | Revision Center | Notes, takeaways, practice, question bank |

---

### Backend — `src/backend/`

**Entry point:** [`app/main.py`](../src/backend/app/main.py)
Instantiates the `FastAPI` app, loads settings via `get_settings()` (pydantic-settings, reads `src/.env`), seeds the demo user on startup (idempotent), and registers all routers.

**Configuration:** [`app/config.py`](../src/backend/app/config.py)
`Settings` (Pydantic BaseSettings) — reads from environment / `.env`:

| Variable | Purpose | Default |
|---|---|---|
| `APP_ENV` | `development` / `production` — controls log level and CORS | `development` |
| `APP_PORT` | Uvicorn port | `8000` |
| `GEMINI_API_KEY` | Google Gemini API key — get one at https://aistudio.google.com/app/apikey | _(required)_ |
| `GEMINI_MODEL` | Gemini model to use | `gemini-1.5-flash` |
| `DEEPSEEK_API_KEY` | Legacy DeepSeek key — preserved for easy restoration; not used at runtime | `""` |
| `DEEPSEEK_MODEL` | Legacy DeepSeek model | `deepseek-chat` |
| `DATABASE_URL` | PostgreSQL DSN | `postgresql://coursegenie:changeme@localhost:5432/coursegenie` |
| `SECRET_KEY` | JWT signing secret — must be changed in production | _(required)_ |
| `JWT_ALGORITHM` | JWT algorithm | `HS256` |
| `JWT_EXPIRE_MINUTES` | Token lifetime | `10080` (7 days) |

---

### API Routes — implemented

**Router registration** ([`app/main.py`](../src/backend/app/main.py)):

```
app
├── api_router              (health + syllabus)
│   ├── GET  /health
│   └── POST /api/v1/syllabus
├── auth.router
│   ├── POST /api/auth/signup
│   ├── POST /api/auth/login
│   └── GET  /api/auth/me
├── courses.router
│   ├── GET   /api/courses
│   ├── GET   /api/courses/{course_id}
│   ├── POST  /api/v1/courses/generate
│   └── PATCH /api/courses/{course_id}
└── topics.router
    ├── POST  /api/topics/{topic_id}/generate-content
    ├── GET   /api/topics/{topic_id}/content
    ├── POST  /api/topics/{topic_id}/generate-quiz
    ├── GET   /api/topics/{topic_id}/quiz
    ├── POST  /api/courses/{course_id}/generate-revision
    ├── GET   /api/courses/{course_id}/revision
    ├── PATCH /api/modules/{module_id}
    └── PATCH /api/topics/{topic_id}
```

#### `GET /health`
Returns liveness status. No auth required.
```json
{ "status": "ok", "service": "CourseGenie AI" }
```

#### `POST /api/auth/signup`
Creates a new user account, hashes the password with bcrypt, and returns a JWT.

#### `POST /api/auth/login`
Verifies credentials (constant-time bcrypt comparison) and returns a JWT.

#### `GET /api/auth/me`
Returns the currently authenticated user's profile. Requires `Authorization: Bearer <token>`.

#### `GET /api/courses`
Returns all courses owned by the authenticated user, newest first. Includes aggregate module/topic counts.

#### `GET /api/courses/{course_id}`
Returns a single course with full module + topic hierarchy, including `has_content` and `has_quiz` flags per topic. Returns 403 if the course belongs to another user.

#### `POST /api/v1/courses/generate`
Sends the syllabus to Google Gemini, which returns a structured hierarchy of modules and topics. Persists to PostgreSQL and returns the full Course object. `owner_id` is set server-side from the JWT.

**Request:**
```json
{ "title": "Intro to Data Structures", "description": "...", "syllabus_text": "Unit 1: Arrays..." }
```
**Response `201`:**
```json
{ "course_id": "uuid", "title": "...", "modules": [...], "model_used": "gemini-1.5-flash" }
```

#### `PATCH /api/courses/{course_id}`
Partial update of title and/or description. Only the course owner may update.

#### `POST /api/topics/{topic_id}/generate-content`
Generates comprehensive learning content for a topic (objectives, explanation, key concepts, examples, summary, further reading). Deletes existing content first, then inserts, in one transaction.

#### `GET /api/topics/{topic_id}/content`
Returns the most recently generated content for a topic.

#### `POST /api/topics/{topic_id}/generate-quiz`
Generates a 5-question MCQ quiz (2 easy / 2 medium / 1 hard). Deletes existing quiz + questions first, then inserts.

#### `GET /api/topics/{topic_id}/quiz`
Returns the most recently generated quiz with all questions.

#### `POST /api/courses/{course_id}/generate-revision`
Generates course-wide revision materials (quick notes, key takeaways, practice questions, question bank). Stored as a `Content` row with `content_type="revision"`.

#### `GET /api/courses/{course_id}/revision`
Returns the most recently generated revision materials.

#### `PATCH /api/modules/{module_id}` / `PATCH /api/topics/{topic_id}`
Partial update of title and/or description. Only the course owner may update.

---

### AI Layer — Google Gemini

The [`DeepSeekClient`](../src/backend/app/services/deepseek_client.py) uses the `openai` Python SDK pointed at Google Gemini's OpenAI-compatible endpoint (`https://generativelanguage.googleapis.com/v1beta/openai/`). All four AI methods follow the same pattern:

1. Build a structured prompt (with explicit JSON schema instructions and strict rules)
2. Call `client.chat.completions.create(model=gemini_model, temperature=0.2–0.3)`
3. Strip any markdown fences from the response (`_extract_json()`)
4. Parse and validate the JSON
5. Raise `ValueError` (→ HTTP 422) on bad structure, `RuntimeError` (→ HTTP 502) on network failure

**Methods:**

| Method | Purpose | Temperature | Max tokens |
|---|---|---|---|
| `generate_course_structure(syllabus_text)` | Parse syllabus into 3–8 modules, each with 2–6 topics | 0.2 | 2048 |
| `generate_topic_content(topic_title, topic_description, course_title)` | Rich learning content (objectives, explanation, key concepts, examples, summary) | 0.3 | 3000 |
| `generate_quiz(topic_title, topic_description, course_title)` | 5-question MCQ quiz with difficulty variation | 0.2 | 2500 |
| `generate_revision(course_title, modules_summary)` | Course-wide revision: quick notes, key takeaways, practice questions, question bank | 0.3 | 3500 |

**AI generation flow:**

```
FastAPI route handler (authenticated — owner verified from JWT)
  → DeepSeekClient.generate_*()
    → _PROMPT.format(...)
    → openai.OpenAI(
        api_key=GEMINI_API_KEY,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
      )
    → chat.completions.create(model="gemini-1.5-flash", messages=[...])
    → _extract_json(raw_response)       ← strip markdown fences
    → json.loads(cleaned)               ← parse
    → validate structure                ← raise ValueError if malformed
    → return (data_dict, model_id)
  → DELETE existing rows (content/quiz) — only after successful AI call
  → INSERT new rows (Course/Module/Topic or Content/Quiz/Questions)
  → commit via get_db() on successful yield
  → return Pydantic response model
```

---

### Authentication Layer — `src/backend/app/services/auth_service.py`

| Concern | Implementation |
|---|---|
| Password hashing | `bcrypt` directly (avoids passlib compatibility issues) — `hash_password()` / `verify_password()` |
| Token creation | `python-jose` — `create_access_token(user_id)` → HS256 JWT with 7-day expiry |
| Token verification | `get_current_user()` — FastAPI `Depends()` — reads `Authorization: Bearer` header, decodes JWT, loads `User` from DB |
| Timing safety | Login always runs `verify_password()` even when user not found (dummy hash) to prevent user-enumeration via timing |

---

### Data Layer — `src/backend/database/`

**Engine:** [`database/connection.py`](../src/backend/database/connection.py)
`create_engine()` reads `DATABASE_URL` from environment. Pool settings: `pool_size=5`, `max_overflow=10`, `pool_pre_ping=True`. SQLite supported for tests (no pooling, `check_same_thread=False`).

**Session:** [`database/session.py`](../src/backend/database/session.py)
`SessionLocal` factory + `get_db()` FastAPI dependency — yields a scoped session with auto-commit on success, rollback on exception.

**ORM Models** ([`database/models.py`](../src/backend/database/models.py)):

```
users            id (UUID PK), name, email, password_hash, role, created_at
  └── courses    id (UUID PK), title, description, syllabus_text, owner_id (FK→users), created_at, updated_at
        └── modules    id, course_id (FK→courses), title, description, order_no
              └── topics     id, module_id (FK→modules), title, description, order_no
                    ├── content    id, topic_id (FK, nullable), course_id (FK, nullable),
                    │              content_type ("lecture"|"revision"), title, body (JSON),
                    │              model_name, created_at
                    │              [uq_content_topic_type: (topic_id, content_type)]
                    │              [uq_content_course_type: (course_id, content_type)]
                    └── quizzes    id, topic_id (FK→topics), title, instructions, created_at
                          └── questions    id, quiz_id (FK→quizzes), question_text, question_type,
                                          options (JSONB), correct_answer, explanation, marks
```

**Migrations:** Alembic — 3 migration versions:
- `0001_initial.py` — creates all tables
- `0002_content_course_id.py` — adds `course_id` column to `content` table for revision anchoring
- `0003_add_password_hash.py` — adds `password_hash` column to `users` table for JWT auth

PostgreSQL uses `JSONB` for `questions.options`; SQLite falls back to plain `JSON` in tests.

---

## Data Flow — Syllabus → Complete Course

```
Professor signs up / logs in → JWT issued
        │
        ▼
React CreateCourse page
  → POST /api/v1/courses/generate  (Authorization: Bearer <token>)
        │
        ▼
FastAPI — owner resolved from JWT (never from client body)
  → DeepSeekClient.generate_course_structure(syllabus_text)
  → Gemini API → gemini-1.5-flash
  → returns validated modules/topics JSON (3–8 modules, 2–6 topics each)
        │
        ▼
FastAPI persists Course + Modules + Topics → PostgreSQL (single transaction)
  → returns GenerateCourseResponse
        │
        ▼
Frontend navigates to /courses/:courseId
  → CourseOverview renders expandable module/topic tree
        │
        ▼ (per topic, on-demand)
POST /api/topics/:id/generate-content  (auth required)
  → DeepSeekClient.generate_topic_content()
  → DELETE existing Content row → INSERT new row (content_type="lecture")

POST /api/topics/:id/generate-quiz  (auth required)
  → DeepSeekClient.generate_quiz()
  → DELETE existing Quiz + Questions → INSERT new Quiz + 5 Question rows

POST /api/courses/:id/generate-revision  (auth required)
  → DeepSeekClient.generate_revision()
  → DELETE existing revision Content → INSERT new row (content_type="revision", course_id set)

Each generation result → served to TopicLearning, QuizPage, RevisionCenter pages
```

---

## Error Handling

| Failure | HTTP Status | Notes |
|---|---|---|
| Missing / invalid JWT | 401 | `get_current_user` raises before route handler runs |
| Wrong owner (course/topic) | 403 | Checked after DB fetch — `course.owner_id != current_user.id` |
| Invalid UUID path param | 400 | Caught before DB query |
| Resource not found | 404 | Topic/course/content/quiz missing |
| Malformed AI JSON | 422 | `ValueError` from `DeepSeekClient._extract_json` / `_validate_structure` |
| AI API down / network failure | 502 | `RuntimeError` from `DeepSeekClient` |
| Pydantic validation failure | 422 | FastAPI built-in |
| Duplicate email on signup | 409 | Checked before DB write |

Internal stack traces and API secrets are never exposed in HTTP responses.

---

## Security Considerations

- All secrets (`GEMINI_API_KEY`, `DATABASE_URL`, `SECRET_KEY`) are environment variables loaded from `src/.env` — this file is in `.gitignore` and never committed
- `src/.env.example` provides a safe template with no real values
- No API keys in any frontend code; `VITE_API_BASE_URL` is the only frontend env var that touches the backend
- `owner_id` is always set server-side from the authenticated JWT — clients cannot supply or forge it
- Login uses constant-time bcrypt comparison even when the user is not found (prevents user-enumeration via timing)
- JWTs expire after 7 days; `SECRET_KEY` must be rotated to invalidate all tokens
- Database uses parameterised queries exclusively via SQLAlchemy ORM — no raw SQL string formatting
- Frontend mock mode (`VITE_USE_MOCKS=true`) is clearly labelled in the UI — mock data is never presented as real AI output

---

## Scalability Notes

- The FastAPI backend is stateless (JWT auth) and can be horizontally scaled behind a load balancer
- Google Gemini API calls are the primary latency bottleneck — each generation request takes 5–30 s; the frontend `GenerationProgress` component handles this with a named-stage UI rather than a spinner
- The React frontend is a static SPA (`dist/`) deployable to any CDN
- TanStack Query's 5-minute stale time prevents redundant AI re-generation calls when navigating between pages
- Alembic migrations version the database schema independently of application deployments
- `pool_pre_ping=True` on the SQLAlchemy engine prevents stale-connection errors on long-idle instances
