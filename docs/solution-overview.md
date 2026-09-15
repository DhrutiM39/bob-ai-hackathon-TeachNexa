# Solution Overview — CourseGenie AI

## What We Built

CourseGenie AI is an AI-powered professor assistant that turns a plain course syllabus into a complete, structured learning experience. A professor signs up, pastes or uploads their syllabus, and the system generates an organised hierarchy of modules and topics, rich learning content per topic, MCQ quizzes, and course-wide revision materials — all persisted to a PostgreSQL database and immediately browsable in the web UI.

---

## How It Works

1. **Professor registers and logs in** — via the React frontend's Auth pages. The backend issues a JWT access token; all subsequent requests are authenticated. Passwords are hashed with bcrypt; tokens use HS256 and expire after 7 days.

2. **Professor submits a syllabus** — via the Create Course page (paste text or file upload). The request carries the JWT and the backend assigns `owner_id` server-side from the authenticated user — clients can never supply or spoof ownership.

3. **FastAPI backend validates the request** — checks token validity, enforces minimum syllabus length via Pydantic schemas.

4. **Google Gemini AI generates course structure** — the `DeepSeekClient` (named historically; now wraps Google Gemini via its OpenAI-compatible endpoint) sends a structured prompt to `gemini-1.5-flash`. The response is a validated JSON hierarchy of 3–8 modules with 2–6 topics each.

5. **Persistence** — FastAPI writes one `Course` row, N `Module` rows, and M `Topic` rows to PostgreSQL inside a single SQLAlchemy transaction.

6. **On-demand content generation** — for each topic, the professor clicks "Generate Content" or "Generate Quiz"; separate authenticated API calls hit Google Gemini for:
   - **Learning content**: objectives, multi-paragraph explanation, key concepts, examples, summary, further reading.
   - **MCQ quizzes**: 5 questions per topic with difficulty variation (2 easy / 2 medium / 1 hard) and answer explanations.
   Results are stored in the `content` and `quizzes` / `questions` tables. Re-generating replaces the old row atomically.

7. **Revision materials** — a single "Generate Revision" call produces course-wide quick notes (6–10 bullets), key takeaways (4–6), a practice question set (3–5 MCQs), and a full question bank (5–8 MCQs). Stored as a revision `Content` row anchored to the course by `course_id`.

8. **Frontend displays everything** — TanStack Query caches results for 5 minutes; React Router navigates between six pages: Dashboard, Create Course, Course Overview, Topic Learning, Quiz, and Revision Center.

---

## Architecture Diagram

> See [`architecture.md`](architecture.md) for the full detailed diagram.

```
Professor (browser)
    │  signup / login → JWT
    ▼
React 18 SPA (Vite 5 · React Router v6 · TanStack Query v5 · Zustand · Axios)
    │  POST /api/auth/signup|login
    │  GET  /api/auth/me
    │  GET  /api/courses
    │  POST /api/v1/courses/generate        ← syllabus in, course out
    │  POST /api/topics/:id/generate-content
    │  POST /api/topics/:id/generate-quiz
    │  POST /api/courses/:id/generate-revision
    ▼
FastAPI backend (Python · pydantic-settings · SQLAlchemy 2.0 · Alembic · python-jose · bcrypt)
    │
    ├──► Google Gemini AI  (OpenAI-compatible endpoint · gemini-1.5-flash model)
    │         └─ returns validated structured JSON (modules/topics, content, quiz, revision)
    │
    └──► PostgreSQL 15 database
              users → courses → modules → topics → content / quizzes → questions
```

---

## Key Design Decisions

| Decision | Rationale |
|---|---|
| **Google Gemini via OpenAI-compatible SDK** | The `openai` Python SDK pointed at `https://generativelanguage.googleapis.com/v1beta/openai/` keeps the integration lightweight (no new SDK). Switching models or providers requires only a config change; the class is named `DeepSeekClient` to preserve easy restoration of the legacy DeepSeek wiring. |
| **JWT authentication with server-side `owner_id`** | All course, module, topic, and revision ownership is resolved from the JWT on the server — clients never supply `owner_id`. This prevents cross-user data access without a separate permissions system. |
| **Regeneration replaces, never duplicates** | `DELETE WHERE topic_id = X AND content_type = 'lecture'` + INSERT happens in one transaction; unique DB indexes (`uq_content_topic_type`, `uq_content_course_type`) enforce at most one active item per parent. The delete only executes after the AI call succeeds — old data is preserved on AI failure. |
| **Revision anchored by `course_id`** | Storing revision content with `Content.course_id` (not `topic_id`) means deleting any topic cannot silently cascade-delete course-level revision materials. A `NULL` `topic_id` on revision rows is intentional. |
| **TanStack Query for server state** | 5-minute stale time prevents redundant AI re-generation calls when navigating between pages. `queryKey` arrays include IDs so cache entries are per-resource, not global. |
| **Dependency injection for the AI client** | `Depends(get_deepseek_client)` in every route that calls AI makes the client trivially replaceable in tests with a `MagicMock` — no network required in CI. |
| **Single SQLAlchemy transaction per generation** | `db.flush()` after each insert (Course → Module → Topic) lets the ORM assign UUIDs before inserting children, while `get_db()`'s commit-on-yield and rollback-on-exception guarantee atomicity. |
| **In-memory SQLite for tests** | All 11 test files use an in-memory SQLite database via a scoped `conftest.py` fixture — no PostgreSQL install required to run the full test suite. |

---

## User Experience Flow

```
1. Sign Up / Log In
   └─ Auth pages → JWT issued → stored in Zustand + localStorage

2. Dashboard
   └─ GET /api/courses → grid of course cards (newest first)
   └─ Empty state with "Create Course" CTA

3. Create Course
   └─ Paste syllabus text (or upload file)
   └─ GenerationProgress component shows named stages:
        "Analysing syllabus…" → "Building modules…" → "Saving course…"
   └─ On success → navigate to /courses/:courseId

4. Course Overview
   └─ Expandable module/topic tree
   └─ Each topic shows has_content / has_quiz badges
   └─ Click topic → Topic Learning page

5. Topic Learning
   └─ "Generate Content" → objectives, explanation, key concepts, examples, summary
   └─ "Generate Quiz" → navigates to Quiz page

6. Quiz Page
   └─ MCQ with 4 options per question
   └─ Navigation between questions
   └─ Score screen on completion with per-question explanations

7. Revision Center
   └─ "Generate Revision" → quick notes, key takeaways, practice questions, question bank
   └─ Paginated question bank for deeper study
```

---

## Development Tooling

**IBM Bob** was used as the AI-assisted development environment throughout the project — for code generation, architecture review, refactoring, and debugging. Bob is a development tool only; it is not a runtime dependency and does not serve any requests in the running application.
