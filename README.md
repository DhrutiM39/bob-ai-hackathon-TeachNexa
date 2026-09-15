# 🚀**CourseGenie AI — An AI Professor Assistant: From Syllabus to Complete Course**


> ⚠️ **Replace everything in `[ ]` brackets with your actual content before submission.**

---

## 👥 Team

| Field | Value |
|---|---|
| **Team Name** | TeachNexa |
| **Track** | AI|
| **Team Lead** | Dhruti Movaliya — 24dcs057@charusat.edu.in |
| **Members** | Riya Kalariya, Hardi Patel, Ishan Kachhadiya |

---

## 🎯 Problem Statement


College professors and educators often spend significant time converting a syllabus into a complete, structured course with lectures, explanations, study materials, assessments, and revision resources. Students may receive fragmented or inconsistent learning content, while faculty struggle to provide personalized and continuously updated learning support within limited time and resources.


---

## 💡 Solution


CourseGenie AI is an AI-powered professor assistant that transforms a course syllabus into a complete, structured learning experience. It uses AI to generate organized course content such as topic explanations, lecture material, study resources, assessments, and revision support, helping professors reduce course preparation time and giving students a consistent learning journey.


---

## ✨ Key Features

- **AI-Powered Course Generation:** Converts a syllabus into structured, topic-wise course content using AI.
- **Personalized Learning Content:** Generates clear explanations, study materials, examples, and learning resources for each topic.
- **AI Assessment Generator:** Automatically creates topic-wise quizzes, questions, and assessments to evaluate student understanding.
- **Smart Revision & Practice:** Provides revision resources, question banks, and practice material based on the course syllabus
- **Professor AI Assistant:** Reduces faculty preparation time by automating repetitive course-content and assessment creation.
---

## 🛠️ Tech Stack

| Category | Technologies |
|---|---|
| **Languages** | Python, JavaScript |
| **Frontend** | React 18, Vite 5, React Router v6, TanStack Query v5, Zustand, Axios |
| **Backend** | FastAPI, SQLAlchemy, Alembic, pydantic-settings |
| **AI Provider** | DeepSeek AI (OpenAI-compatible API via `openai` SDK) |
| **Database** | PostgreSQL |
| **Dev Tooling** | IBM Bob (AI-assisted development environment), Git, GitHub |

---

## 📁 Repository Structure

```
├── src/                  # All source code
├── docs/                 # Written documentation
│   ├── problem-statement.md
│   ├── solution-overview.md
│   ├── architecture.md
│   └── setup-guide.md
├── demo/                 # Demo artifacts
│   ├── screenshots/      # App screenshots
│   └── demo-video-link.txt  # Link to demo video
├── presentation/         # Slide deck
└── submission.yaml       # Structured submission metadata
```

---

## ⚡ How to Run

> Full step-by-step instructions: [`docs/setup-guide.md`](docs/setup-guide.md)

```bash
# 1. Install Python deps
python -m venv .venv && .venv\Scripts\Activate.ps1   # Windows
# source .venv/bin/activate                           # macOS/Linux
pip install -r src/backend/requirements.txt

# 2. Configure environment
cp src/.env.example src/.env
# Edit src/.env — set DEEPSEEK_API_KEY and DATABASE_URL

# 3. Start PostgreSQL (Docker)
docker run -d --name coursegenie-db \
  -e POSTGRES_USER=coursegenie -e POSTGRES_PASSWORD=changeme \
  -e POSTGRES_DB=coursegenie -p 5432:5432 postgres:15-alpine

# 4. Run migrations + seed demo user
alembic -c src/backend/alembic.ini upgrade head

# 5. Start backend
uvicorn backend.app.main:app --reload --port 8000 --app-dir src

# 6. Start frontend (new terminal)
cd src/frontend && npm install && npm run dev
# Open http://localhost:3000
```

---

## 🖥️ Demo

| Artifact | Link |
|---|---|
| 📹 Demo Video | [See demo/demo-video-link.txt](demo/demo-video-link.txt) |
| 🌐 Live Demo | [See demo/live-demo-url.txt](demo/live-demo-url.txt) |
| 🖼️ Screenshots | [See demo/screenshots/](demo/screenshots/) |
| 📊 Presentation | [See presentation/slides.pdf](presentation/) |

---

## ⚠️ Known Limitations

- Authentication is not yet implemented — a fixed demo `owner_id` UUID is used until auth is added.
- File-upload syllabus parsing (PDF/DOCX) reads the raw bytes; rich text extraction is not implemented.
- Content generation can take 10–30 seconds per topic depending on DeepSeek API latency.
- No production deployment — the app runs locally; no IBM Cloud or other cloud hosting is configured.

---

## 🏅 What We're Most Proud Of

We are most proud of building a fully wired end-to-end pipeline — from a plain syllabus paste to a browsable course with per-topic content, quizzes, and revision materials — with every generation operation guaranteed to replace (not duplicate) old rows, proven by 148 passing tests covering replacement, rollback safety, and constraint enforcement.

---
