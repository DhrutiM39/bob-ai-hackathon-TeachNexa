# Architecture — CourseGenie AI

## Overview

CourseGenie AI is an AI Professor Assistant that transforms a plain college syllabus into a complete, structured course — modules, topics, learning content, quizzes, and revision materials — powered by **DeepSeek AI** (via its OpenAI-compatible API).

---

## System Architecture

```mermaid
graph TD
    subgraph Browser
        A[User]
        B["React 18 Frontend\n(Vite · React Router v6\nTanStack Query · Zustand\nCSS Modules)"]
    end

    subgraph "FastAPI Backend  :8000"
        C["main.py\nFastAPI app\n+ CORS + Settings"]
        D["GET /health\nLiveness check"]
        E["POST /api/v1/syllabus\nSyllabus ingest & validation"]
        F["Courses router\nGET /api/courses\nGET /api/courses/:id\nPOST /api/v1/courses/generate"]
        G["Topics router\nPOST /api/topics/:id/generate-content\nGET  /api/topics/:id/content\nPOST /api/topics/:id/generate-quiz\nGET  /api/topics/:id/quiz\nPOST /api/courses/:id/generate-revision\nGET  /api/courses/:id/revision"]
        H["SyllabusService\nbusiness logic · ID generation"]
        I["pydantic-settings\nConfig · .env loader"]
    end

    subgraph "DeepSeek AI"
        J["DeepSeekClient\nopenai SDK (OpenAI-compatible)\ngenerate_course_structure()\ngenerate_topic_content()\ngenerate_quiz()\ngenerate_revision()"]
        K["DeepSeek Model\n(deepseek-chat)"]
    end

    subgraph "Data Layer"
        L["SQLAlchemy ORM\nSession · Engine"]
        M[("PostgreSQL\ncoursegenie DB")]
        N["Alembic\nmigrations"]
    end

    A -->|"HTTPS · JSON"| B
    B -->|"REST / Axios\nVITE_API_BASE_URL"| C
    C --> D
    C --> E
    C --> F
    C --> G
    E --> H
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
| Server state | TanStack Query v5 — `useCourses`, `useTopicContent`, `useQuiz`, `useRevision` hooks |
| UI state | Zustand — isolated to the syllabus-generation flow store (`useGenerationStore`) |
| Styling | CSS Modules + centralized design tokens (`src/styles/tokens.css`) |
| HTTP client | Axios — base URL read from `VITE_API_BASE_URL` env var; no API keys in frontend code |
| Adapters | `services/adapters/` — normalize backend field names defensively (snake_case / camelCase / fallbacks) |
| Mocks | `VITE_USE_MOCKS=true` serves fixture data from `mocks/mockData.js` — clearly labelled in UI |

**Routes served:**

| URL | Page |
|---|---|
| `/` | Dashboard — course grid, empty state |
| `/create` | Create Course — syllabus input + inline AI generation progress |
| `/courses/:courseId` | Course Overview — expandable module/topic tree |
| `/courses/:courseId/topics/:topicId` | Topic Learning — content + sidebar |
| `/courses/:courseId/topics/:topicId/quiz` | Quiz — MCQ, navigation, score screen |
| `/courses/:courseId/revision` | Revision Center — notes, takeaways, practice, question bank |

---

### Backend — `src/backend/`

**Entry point:** [`app/main.py`](../src/backend/app/main.py)  
Instantiates the `FastAPI` app, loads settings via `get_settings()` (pydantic-settings, reads `src/.env`), and registers all routers.

**Configuration:** [`app/config.py`](../src/backend/app/config.py)  
`Settings` (Pydantic BaseSettings) — reads from environment / `.env`:

| Variable | Purpose |
|---|---|
| `APP_ENV` | `development` / `production` |
| `APP_PORT` | Uvicorn port (default `8000`) |
| `DEEPSEEK_API_KEY` | DeepSeek API credential — get one at https://platform.deepseek.com/api_keys |
| `DEEPSEEK_MODEL` | Model to use (default `deepseek-chat`) |
| `DATABASE_URL` | PostgreSQL DSN (default `postgresql://postgres:postgres@localhost:5432/coursegenie`) |

---

### API Routes — implemented

**Router registration** ([`app/main.py`](../src/backend/app/main.py)):

```
app
├── api_router          (health + syllabus)
│   ├── GET  /health
│   └── POST /api/v1/syllabus
├── courses.router
│   ├── GET  /api/courses
│   ├── GET  /api/courses/{course_id}
│   └── POST /api/v1/courses/generate
└── topics.router
    ├── POST /api/topics/{topic_id}/generate-content
    ├── GET  /api/topics/{topic_id}/content
    ├── POST /api/topics/{topic_id}/generate-quiz
    ├── GET  /api/topics/{topic_id}/quiz
    ├── POST /api/courses/{course_id}/generate-revision
    └── GET  /api/courses/{course_id}/revision
```

#### `GET /health`
Returns liveness status.

```json
{ "status": "ok", "service": "CourseGenie AI" }
```

#### `POST /api/v1/syllabus`
Accepts a raw syllabus and returns a validated, ID-stamped record.

#### `GET /api/courses`
Returns all courses with aggregate module/topic counts.

#### `GET /api/courses/{course_id}`
Returns a single course with full module + topic hierarchy, including `has_content` and `has_quiz` flags per topic.

#### `POST /api/v1/courses/generate`
Sends the syllabus to DeepSeek, which returns a structured hierarchy of modules and topics. Persists to PostgreSQL and returns the full Course object.

**Request:**
```json
{ "title": "Intro to AI", "syllabus_text": "Week 1: ...", "owner_id": "uuid" }
```
**Response `201`:**
```json
{ "course_id": "uuid", "title": "...", "modules": [...], "model_used": "deepseek-chat" }
```

#### `POST /api/topics/{topic_id}/generate-content`
Generates comprehensive learning content for a topic (objectives, explanation, key concepts, examples, summary, further reading). Persists to the `content` table.

#### `GET /api/topics/{topic_id}/content`
Returns the most recently generated content for a topic.

#### `POST /api/topics/{topic_id}/generate-quiz`
Generates a 5-question MCQ quiz. Persists Quiz + Question rows.

#### `GET /api/topics/{topic_id}/quiz`
Returns the most recently generated quiz with all questions.

#### `POST /api/courses/{course_id}/generate-revision`
Generates course-wide revision materials (quick notes, key takeaways, practice questions, question bank). Stored as a `Content` row with `content_type="revision"`.

#### `GET /api/courses/{course_id}/revision`
Returns the most recently generated revision materials for a course.

---

### AI Layer — DeepSeek AI

The [`DeepSeekClient`](../src/backend/app/services/deepseek_client.py) uses the `openai` Python SDK pointed at DeepSeek's OpenAI-compatible endpoint (`https://api.deepseek.com`). All four AI methods follow the same pattern:

1. Build a structured prompt (with explicit JSON schema instructions)
2. Call `client.chat.completions.create()` with low temperature
3. Strip any markdown fences from the response
4. Parse and validate the JSON
5. Raise `ValueError` (→ HTTP 422) on bad structure, `RuntimeError` (→ HTTP 502) on network failure

**Methods:**

| Method | Purpose | Returns |
|---|---|---|
| `generate_course_structure(syllabus_text)` | Parse syllabus into modules/topics | `list[dict]` of modules |
| `generate_topic_content(topic_title, topic_description, course_title)` | Rich learning content | dict with objectives, explanation, key concepts, examples, summary |
| `generate_quiz(topic_title, topic_description, course_title)` | 5-question MCQ quiz | dict with title + questions list |
| `generate_revision(course_title, modules_summary)` | Course-wide revision materials | dict with quick_notes, key_takeaways, practice_questions, question_bank |

**AI flow:**

```
FastAPI route handler
  → DeepSeekClient.generate_*()
    → _PROMPT.format(...)
    → openai.OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
    → chat.completions.create(model=DEEPSEEK_MODEL, messages=[...])
    → _extract_json(raw_response)       ← strip markdown fences
    → json.loads(cleaned)               ← parse
    → validate structure                ← raise ValueError if malformed
    → return (data_dict, model_id)
  → persist to PostgreSQL
  → return Pydantic response model
```

---

### Data Layer — `src/backend/database/`

**Engine:** [`database/connection.py`](../src/backend/database/connection.py)  
`create_engine()` reads `DATABASE_URL` from environment. Pool settings: `pool_size=5`, `max_overflow=10`, `pool_pre_ping=True`. SQLite supported for tests (no pooling, `check_same_thread=False`).

**Session:** [`database/session.py`](../src/backend/database/session.py)  
`SessionLocal` factory + `get_db()` FastAPI dependency — yields a scoped session with auto-commit on success, rollback on exception.

**ORM Models** ([`database/models.py`](../src/backend/database/models.py)):

```
users            id (UUID PK), name, email, role, created_at
  └── courses    id (UUID PK), title, description, syllabus_text, owner_id (FK), created_at, updated_at
        └── modules    id, course_id (FK), title, description, order_no
              └── topics     id, module_id (FK), title, description, order_no
                    ├── content    id, topic_id (FK), content_type, title, body (JSON), model_name, created_at
                    └── quizzes    id, topic_id (FK), title, instructions, created_at
                          └── questions    id, quiz_id (FK), question_text, question_type,
                                          options (JSONB/JSON), correct_answer, explanation, marks
```

**Migrations:** Alembic — `migrations/versions/0001_initial.py` creates all tables. PostgreSQL uses `JSONB` for `questions.options`; SQLite falls back to plain `JSON` in tests.

---

## Data Flow — Syllabus → Complete Course

```
Professor pastes syllabus
        │
        ▼
React CreateCourse page
  → POST /api/v1/courses/generate
        │
        ▼
FastAPI CourseService
  → DeepSeekClient.generate_course_structure(syllabus_text)
  → DeepSeek API → deepseek-chat model
  → returns validated modules/topics JSON
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
POST /api/topics/:id/generate-content
  → DeepSeekClient.generate_topic_content()
  → Persists to content table (content_type="lecture")

POST /api/topics/:id/generate-quiz
  → DeepSeekClient.generate_quiz()
  → Persists Quiz row + Question rows (cascade)

POST /api/courses/:id/generate-revision
  → DeepSeekClient.generate_revision()
  → Persists to content table (content_type="revision")

Each generation: results stored → served to TopicLearning, QuizPage, RevisionCenter pages
```

---

## Error Handling

| Failure | HTTP Status | Notes |
|---|---|---|
| Invalid UUID path param | 400 | Caught before DB query |
| Resource not found | 404 | Topic/course/content/quiz missing |
| Malformed AI JSON | 422 | `ValueError` from `DeepSeekClient` |
| AI API down / network failure | 502 | `RuntimeError` from `DeepSeekClient` |
| Pydantic validation failure | 422 | FastAPI built-in |
| Missing required FK (owner_id) | 400 | Checked before DB write |

Internal stack traces and API secrets are never exposed in HTTP responses.

---

## Security Considerations

- All secrets (`DEEPSEEK_API_KEY`, `DATABASE_URL`) are environment variables loaded from `src/.env` — this file is in `.gitignore` and never committed
- `src/.env.example` provides a safe template with no real values
- No API keys are present in any frontend code; `VITE_API_BASE_URL` is the only frontend env var that touches the backend
- Frontend mock mode (`VITE_USE_MOCKS=true`) is clearly labelled in the UI — mock data is never presented as real AI output
- `pydantic-settings` validates all config at startup — the app fails fast on missing required credentials
- Database uses parameterized queries exclusively via SQLAlchemy ORM — no raw SQL string formatting

---

## Scalability Notes

- The FastAPI backend is stateless and can be horizontally scaled behind a load balancer
- DeepSeek API calls are the primary latency bottleneck — each generation request can take 5–30 s; the frontend `GenerationProgress` component handles this with a named-stage UI rather than a spinner
- The React frontend is a static SPA (`dist/`) deployable to any CDN
- TanStack Query's 5-minute stale time prevents redundant AI re-generation calls when navigating between pages
- Alembic migrations version the database schema independently of application deployments
