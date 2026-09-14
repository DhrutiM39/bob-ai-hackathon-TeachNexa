# Architecture — CourseGenie AI

## Overview

CourseGenie AI is an AI Professor Assistant that transforms a plain college syllabus into a complete, structured course — modules, topics, learning content, quizzes, and revision materials — powered by IBM watsonx.ai.

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
        F["Courses router\n(planned)"]
        G["Topics router\n(planned)"]
        H["SyllabusService\nbusiness logic · ID generation"]
        I["pydantic-settings\nConfig · .env loader"]
    end

    subgraph "IBM watsonx.ai"
        J["WatsonxClient\n(planned)\nibm-watsonx-ai SDK"]
        K["Foundation Model\n(e.g. ibm/granite-13b-instruct)"]
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
    G -->|"generate content\ngenerate quiz"| J
    J --> K
    K -->|"structured JSON\nresponse"| J
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
Instantiates the `FastAPI` app, loads settings via `get_settings()` (pydantic-settings, reads `src/.env`), and registers `api_router`.

**Configuration:** [`app/config.py`](../src/backend/app/config.py)  
`Settings` (Pydantic BaseSettings) — reads from environment / `.env`:

| Variable | Purpose |
|---|---|
| `APP_ENV` | `development` / `production` |
| `APP_PORT` | Uvicorn port (default `8000`) |
| `WATSONX_API_KEY` | IBM watsonx.ai credential |
| `WATSONX_PROJECT_ID` | watsonx.ai project scope |
| `WATSONX_URL` | Inference endpoint (default `us-south.ml.cloud.ibm.com`) |
| `DATABASE_URL` | PostgreSQL DSN (default `postgresql://postgres:postgres@localhost:5432/coursegenie`) |

---

### API Routes — current state

**Router registration** ([`app/api/__init__.py`](../src/backend/app/api/__init__.py)):

```
api_router
├── health_router       → (no prefix)
└── syllabus_router     → /api/v1
```

#### `GET /health`
Returns liveness status. Used by orchestrators and the frontend health-check.

```json
{ "status": "ok", "service": "CourseGenie AI" }
```

#### `POST /api/v1/syllabus`
Accepts a raw syllabus and returns a validated, ID-stamped record.  
Handled by [`SyllabusService.process_syllabus()`](../src/backend/app/services/syllabus_service.py).

**Request:**
```json
{ "course_name": "Intro to AI", "syllabus_text": "Week 1: Foundations..." }
```
**Response `201`:**
```json
{
  "status": "accepted",
  "syllabus_id": "cg-a3f2c91b-d4e80012",
  "course_name": "Intro to AI",
  "syllabus_text": "Week 1: Foundations...",
  "character_count": 512,
  "message": "Syllabus for 'Intro to AI' received and validated successfully."
}
```

**Planned (Milestone 3+):**

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/v1/course/generate` | Generate full course structure from syllabus |
| `GET` | `/api/v1/courses` | List user's courses |
| `GET` | `/api/v1/courses/:id` | Get single course with modules + topics |
| `POST` | `/api/v1/topics/:id/generate-content` | Trigger watsonx.ai content generation |
| `GET` | `/api/v1/topics/:id/content` | Fetch generated content |
| `POST` | `/api/v1/topics/:id/generate-quiz` | Trigger quiz generation |
| `GET` | `/api/v1/topics/:id/quiz` | Fetch quiz |
| `POST` | `/api/v1/topics/:id/generate-revision` | Trigger revision generation |
| `GET` | `/api/v1/courses/:id/revision` | Fetch revision center data |

---

### AI Layer — IBM watsonx.ai (planned Milestone 3)

The `WatsonxClient` will use the `ibm-watsonx-ai` Python SDK, authenticated via `WATSONX_API_KEY` + `WATSONX_PROJECT_ID`. The client will be invoked from topic/quiz/revision service functions to call a foundation model (e.g. `ibm/granite-13b-instruct`) with structured prompts and return JSON-parsed results.

---

### Data Layer — `src/backend/database/`

**Engine:** [`database/connection.py`](../src/backend/database/connection.py)  
`create_engine()` reads `DATABASE_URL` from environment. Pool settings: `pool_size=5`, `max_overflow=10`, `pool_pre_ping=True`. SQLite supported for tests (no pooling, `check_same_thread=False`).

**Session:** [`database/session.py`](../src/backend/database/session.py)  
`SessionLocal` factory + `get_db()` FastAPI dependency — yields a scoped session with auto-commit/rollback.

**ORM Models** ([`database/models.py`](../src/backend/database/models.py)):

```
users            id (UUID PK), name, email, role, created_at
  └── courses    id (UUID PK), title, description, syllabus_text, owner_id (FK), created_at, updated_at
        └── modules    id, course_id (FK), title, description, order_no
              └── topics     id, module_id (FK), title, description, order_no
                    ├── content    id, topic_id (FK), content_type, title, body, model_name, created_at
                    └── quizzes    id, topic_id (FK), title, instructions, created_at
                          └── questions    id, quiz_id (FK), question_text, question_type,
                                          options (JSON), correct_answer, explanation, marks
```

**Migrations:** Alembic — `migrations/versions/0001_initial.py` creates all tables. PostgreSQL uses `JSONB` for `questions.options`; SQLite falls back to plain `JSON`.

---

## Data Flow — Syllabus → Course

```
Professor pastes syllabus
        │
        ▼
React CreateCourse page
  → POST /api/v1/syllabus          (current — validates & IDs the text)
  → POST /api/v1/course/generate   (planned — returns module/topic tree)
        │
        ▼
FastAPI CourseService
  → prompt-engineering layer
  → WatsonxClient.generate(prompt)
        │
        ▼
IBM watsonx.ai Foundation Model
  → returns structured JSON (modules, topics, objectives)
        │
        ▼
FastAPI persists Course + Modules + Topics → PostgreSQL
  → returns course ID
        │
        ▼
Frontend navigates to /courses/:courseId
  → CourseOverview renders expandable module/topic tree
        │
        ▼ (per topic, on-demand)
POST /api/v1/topics/:id/generate-content
POST /api/v1/topics/:id/generate-quiz
POST /api/v1/topics/:id/generate-revision
  → each triggers a separate watsonx.ai call
  → results stored in content / quizzes / questions tables
  → served to TopicLearning, QuizPage, RevisionCenter pages
```

---

## Security Considerations

- All secrets (`WATSONX_API_KEY`, `DATABASE_URL`) are environment variables loaded from `src/.env` — this file is in `.gitignore` and never committed
- `src/.env.example` provides a safe template with no real values
- No API keys are present in any frontend code; `VITE_API_BASE_URL` is the only frontend env var that touches the backend
- Frontend mock mode (`VITE_USE_MOCKS=true`) is clearly labelled in the UI — mock data is never presented as real AI output
- `pydantic-settings` validates all config at startup — the app fails fast on missing required credentials
- Database uses parameterized queries exclusively via SQLAlchemy ORM — no raw SQL string formatting

---

## Scalability Notes

- The FastAPI backend is stateless and can be horizontally scaled behind a load balancer (e.g. IBM Code Engine, Railway)
- IBM watsonx.ai calls are the primary latency bottleneck — each generation request can take 5–30 s; the frontend GenerationProgress component handles this with a named-stage UI rather than a spinner
- The React frontend is a static SPA (`dist/`) deployable to any CDN (IBM Cloud Object Storage + CDN, Netlify, Vercel)
- TanStack Query's 5-minute stale time prevents redundant AI re-generation calls when navigating between pages
- Alembic migrations version the database schema independently of application deployments
