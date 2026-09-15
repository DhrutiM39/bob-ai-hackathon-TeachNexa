# 🎓 CourseGenie AI — AI Professor Assistant: From Syllabus to Complete Course

> An end-to-end AI-powered platform that transforms a plain college syllabus into a fully structured course with topic explanations, quizzes, and revision materials.

---

## 👥 Team

| Field | Value |
|---|---|
| **Team Name** | TeachNexa |
| **Track** | AI |
| **Team Lead** | Dhruti Movaliya — 24dcs057@charusat.edu.in |
| **Members** | Riya Kalariya (24it037@charusat.edu.in), Hardi Patel (24dcs072@charusat.edu.in), Ishan Kachhadiya (24it034@charusat.edu.in) |

---

## 🎯 Problem Statement

College professors and educators spend significant time converting a syllabus into a complete, structured course with lectures, explanations, study materials, assessments, and revision resources. Students may receive fragmented or inconsistent learning content, while faculty struggle to provide personalized and continuously updated learning support within limited time and resources.

---

## 💡 Solution

**CourseGenie AI** is an AI-powered professor assistant that transforms a course syllabus into a complete, structured learning experience. It uses **Google Gemini AI** (via an OpenAI-compatible API) to generate organized, topic-wise course content — including learning objectives, detailed explanations, key concepts, worked examples, MCQ quizzes, and course-wide revision materials — all persisted to PostgreSQL and served through a modern React frontend.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| **AI Course Generation** | Paste a syllabus → AI decomposes it into 3–8 modules, each with 2–6 ordered topics |
| **Topic Learning Content** | Per-topic: learning objectives, multi-paragraph explanation, key concepts, examples, summary, further reading |
| **AI Quiz Generator** | 5-question MCQ quiz per topic with difficulty variation (2 easy / 2 medium / 1 hard) and explanations |
| **Revision Center** | Course-wide quick notes, key takeaways, practice questions, and a full question bank |
| **JWT Authentication** | Signup / login / `/me` — bcrypt password hashing + HS256 JWT tokens; full per-user course ownership |
| **Edit Support** | `PATCH` endpoints for course, module, and topic metadata |
| **Idempotent Generation** | Re-generating content or quizzes replaces (never duplicates) existing rows, enforced by DB unique constraints |

---

## 🛠️ Tech Stack

| Category | Technologies |
|---|---|
| **Languages** | Python 3.11+, JavaScript (ESM) |
| **Frontend** | React 18, Vite 5, React Router v6, TanStack Query v5, Zustand, Axios, CSS Modules |
| **Backend** | FastAPI, Uvicorn, SQLAlchemy 2.0, Alembic, pydantic-settings, python-jose, bcrypt |
| **AI Provider** | Google Gemini (`gemini-1.5-flash`) via OpenAI-compatible API (`openai` SDK) |
| **Database** | PostgreSQL 15 (JSONB for quiz options); SQLite for tests |
| **Dev Tooling** | IBM Bob (AI-assisted development), Git, GitHub, Docker, pytest |

---

## 📁 Repository Structure

```
bob-ai-hackathon-TeachNexa/
├── src/
│   ├── .env.example                    # Environment variable template
│   ├── backend/
│   │   ├── app/
│   │   │   ├── main.py                 # FastAPI app entry point + lifespan seed
│   │   │   ├── config.py               # pydantic-settings (Gemini, DB, JWT)
│   │   │   ├── seed.py                 # Demo user idempotent seed
│   │   │   ├── api/
│   │   │   │   ├── health.py           # GET /health
│   │   │   │   └── syllabus.py         # POST /api/v1/syllabus
│   │   │   ├── routers/
│   │   │   │   ├── auth.py             # POST /api/auth/signup|login, GET /api/auth/me
│   │   │   │   ├── courses.py          # GET/PATCH /api/courses, POST /api/v1/courses/generate
│   │   │   │   └── topics.py           # POST/GET content, quiz, revision; PATCH module/topic
│   │   │   ├── schemas/                # Pydantic request/response models
│   │   │   └── services/
│   │   │       ├── auth_service.py     # JWT create/verify, bcrypt hash/verify
│   │   │       └── deepseek_client.py  # Gemini AI wrapper (4 generation methods)
│   │   ├── database/
│   │   │   ├── models.py               # ORM: User, Course, Module, Topic, Content, Quiz, Question
│   │   │   ├── connection.py           # SQLAlchemy engine + Base
│   │   │   └── session.py              # get_db() FastAPI dependency
│   │   ├── migrations/
│   │   │   └── versions/               # Alembic migrations (0001–0003)
│   │   ├── tests/                      # 148+ tests across 11 test files
│   │   └── requirements.txt
│   └── frontend/
│       ├── src/
│       │   ├── pages/                  # Dashboard, CreateCourse, CourseOverview,
│       │   │   │                       # TopicLearning, QuizPage, RevisionCenter
│       │   ├── services/api/           # syllabusService, courseService, topicService, quizService
│       │   ├── store/                  # Zustand: useGenerationStore
│       │   └── components/             # Button, Modal, Skeleton, StepIndicator, etc.
│       ├── package.json
│       └── vite.config.js
├── docs/
│   ├── architecture.md                 # Full system architecture with Mermaid diagram
│   ├── problem-statement.md
│   ├── solution-overview.md
│   └── setup-guide.md                  # Step-by-step setup instructions
├── demo/
│   ├── demo-video-link.txt
│   ├── live-demo-url.txt
│   └── screenshots/
├── presentation/
└── submission.yaml
```

---

## ⚡ Quick Start

> Full setup: [`docs/setup-guide.md`](docs/setup-guide.md)

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ (or Docker)
- Google Gemini API key — [get one free at Google AI Studio](https://aistudio.google.com/app/apikey)

### 1 — Clone & Install

```bash
git clone https://github.com/your-org/bob-ai-hackathon-TeachNexa.git
cd bob-ai-hackathon-TeachNexa

# Python virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1        # Windows PowerShell
# source .venv/bin/activate        # macOS / Linux

pip install -r src/backend/requirements.txt
```

### 2 — Configure Environment

```bash
cp src/.env.example src/.env
# Edit src/.env — set GEMINI_API_KEY, DATABASE_URL, SECRET_KEY
```

| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | Google Gemini API key (required for AI generation) |
| `DATABASE_URL` | PostgreSQL DSN, e.g. `postgresql://coursegenie:changeme@localhost:5432/coursegenie` |
| `SECRET_KEY` | Random string for JWT signing — `python -c "import secrets; print(secrets.token_hex(32))"` |
| `GEMINI_MODEL` | Model override (default: `gemini-1.5-flash`) |

### 3 — Start PostgreSQL

```bash
# Docker (recommended)
docker run -d --name coursegenie-db \
  -e POSTGRES_USER=coursegenie -e POSTGRES_PASSWORD=changeme \
  -e POSTGRES_DB=coursegenie -p 5432:5432 postgres:15-alpine
```

### 4 — Migrate Database

```bash
alembic -c src/backend/alembic.ini upgrade head
```

### 5 — Start Backend

```bash
uvicorn backend.app.main:app --reload --port 8000 --app-dir src
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

### 6 — Start Frontend

```bash
cd src/frontend
npm install
npm run dev
# App: http://localhost:3000
```

---

## 🗺️ API Reference

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Liveness check |
| `POST` | `/api/auth/signup` | Register new user → JWT |
| `POST` | `/api/auth/login` | Login → JWT |
| `GET` | `/api/auth/me` | Current user profile |
| `GET` | `/api/courses` | List courses (auth required) |
| `GET` | `/api/courses/{id}` | Course detail with full module/topic tree |
| `POST` | `/api/v1/courses/generate` | Generate course from syllabus via AI |
| `PATCH` | `/api/courses/{id}` | Update course title/description |
| `POST` | `/api/topics/{id}/generate-content` | Generate topic learning content |
| `GET` | `/api/topics/{id}/content` | Retrieve topic content |
| `POST` | `/api/topics/{id}/generate-quiz` | Generate 5-question MCQ quiz |
| `GET` | `/api/topics/{id}/quiz` | Retrieve topic quiz |
| `POST` | `/api/courses/{id}/generate-revision` | Generate course revision materials |
| `GET` | `/api/courses/{id}/revision` | Retrieve revision materials |
| `PATCH` | `/api/modules/{id}` | Update module title/description |
| `PATCH` | `/api/topics/{id}` | Update topic title/description |

---

## 🗄️ Data Model

```
users
  └── courses  (owner_id FK → users)
        └── modules  (course_id FK → courses)
              └── topics  (module_id FK → modules)
                    ├── content  (topic_id FK — type: "lecture")
                    │   [course_id FK — type: "revision"]
                    └── quizzes  (topic_id FK)
                          └── questions  (quiz_id FK, options: JSONB)
```

---

## 🧪 Tests

```bash
# Run full test suite (uses in-memory SQLite — no PostgreSQL needed)
pytest -v

# Run a specific file
pytest src/backend/tests/test_generate_endpoint.py -v
```

The suite covers: auth flows, course CRUD, topic content/quiz/revision generation, idempotent replacement, DB constraints, ownership enforcement, and file-upload edge cases.

---

## 🖥️ Demo

| Artifact | Link |
|---|---|
| 📹 Demo Video | [See demo/demo-video-link.txt](demo/demo-video-link.txt) |
| 🌐 Live Demo | [See demo/live-demo-url.txt](demo/live-demo-url.txt) |
| 🖼️ Screenshots | [demo/screenshots/](demo/screenshots/) |
| 📊 Presentation | [presentation/](presentation/) |

---

## ⚠️ Known Limitations

- **No production deployment** — the app runs locally; no cloud hosting is configured.
- **Content generation latency** — each AI generation call takes 5–30 seconds depending on Google Gemini API response time; the frontend shows a named-stage progress indicator.
- **File-upload syllabus parsing** — raw bytes are read; rich PDF/DOCX text extraction is not implemented.
- **Mock mode** — `VITE_USE_MOCKS=true` serves fixture data from `mocks/mockData.js`; this is clearly labelled in the UI and never presented as real AI output.

---

## 🏅 What We're Most Proud Of

We are most proud of building a **fully wired end-to-end pipeline** — from a plain syllabus paste to a browsable course with per-topic content, quizzes, and revision materials. Every generation operation is **guaranteed to replace (not duplicate)** old rows, enforced by database-level unique constraints, and proven by a comprehensive test suite covering replacement semantics, rollback safety, ownership enforcement, and constraint violations.

---

## 📄 License

This project was built for the IBM Bob AI Hackathon. See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.
