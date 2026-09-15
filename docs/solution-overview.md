# Solution Overview

## What We Built

CourseGenie AI is an AI-powered professor assistant that turns a plain course syllabus into a complete, structured learning experience. A professor pastes or uploads their syllabus, and the system generates an organized hierarchy of modules and topics, rich learning content per topic, MCQ quizzes, and course-wide revision materials — all persisted to a PostgreSQL database and immediately browsable in the web UI.

## How It Works

1. **Professor submits a syllabus** — via the React frontend's Create Course page (paste text or file upload).
2. **FastAPI backend validates the request** — checks owner ID, enforces minimum syllabus length.
3. **DeepSeek AI generates course structure** — the `DeepSeekClient` sends a structured prompt to the DeepSeek chat completions API (`deepseek-chat` model). The response is a validated JSON hierarchy of modules and topics.
4. **Persistence** — FastAPI writes one `Course` row, N `Module` rows, and M `Topic` rows to PostgreSQL inside a single SQLAlchemy transaction.
5. **On-demand content generation** — for each topic, the professor clicks "Generate Content" or "Generate Quiz"; separate API calls hit DeepSeek for learning content (objectives, explanation, key concepts, examples) and MCQ quizzes. Results are stored in the `content` and `quizzes` / `questions` tables.
6. **Revision materials** — a single "Generate Revision" call produces course-wide quick notes, key takeaways, a practice question set, and a full question bank, stored as a revision `Content` row anchored to the course.
7. **Frontend displays everything** — TanStack Query caches results; React Router navigates between Dashboard, Course Overview, Topic Learning, Quiz, and Revision Center pages.

## Architecture Diagram

> See [`architecture.md`](architecture.md) for the full detailed diagram.

```
Professor (browser)
    │
    ▼
React 18 SPA (Vite 5 · React Router v6 · TanStack Query v5 · Zustand · Axios)
    │  POST /api/v1/courses/generate
    │  POST /api/topics/:id/generate-content
    │  POST /api/topics/:id/generate-quiz
    │  POST /api/courses/:id/generate-revision
    ▼
FastAPI backend (Python · pydantic-settings · SQLAlchemy · Alembic)
    │
    ├──► DeepSeek AI API  (OpenAI-compatible · deepseek-chat model)
    │         └─ returns validated structured JSON
    │
    └──► PostgreSQL database
              users → courses → modules → topics → content / quizzes → questions
```

## Key Design Decisions

| Decision | Rationale |
|---|---|
| **DeepSeek AI via OpenAI-compatible SDK** | The `openai` Python SDK pointed at `https://api.deepseek.com` keeps the integration lightweight (no new SDK, one dependency). Switching models requires only a config change. |
| **Regeneration replaces, never duplicates** | `DELETE WHERE topic_id = X AND content_type = 'lecture'` + INSERT in one transaction; unique DB indexes enforce at most one active item per parent. Old data is preserved on AI failure (delete happens after a successful AI call). |
| **Revision anchored by `course_id`** | Storing revision content with `Content.course_id` (not `topic_id`) means deleting any topic cannot silently cascade-delete course-level revision materials. |
| **TanStack Query for server state** | 5-minute stale time prevents redundant AI re-generation calls when navigating between pages. |
| **Dependency injection for DeepSeekClient** | `Depends(get_deepseek_client)` in every route that calls AI makes the client trivially replaceable in tests with a `MagicMock` — no network required in CI. |

## Development Tooling

IBM Bob was used as the AI-assisted development environment throughout the project — for code generation, architecture review, and debugging. Bob is a development tool only; it is not a runtime dependency and does not serve any requests in the deployed application.
