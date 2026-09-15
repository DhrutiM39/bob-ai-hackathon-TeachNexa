# Problem Statement — CourseGenie AI

## Background

Higher education institutions around the world rely on course syllabi as the single source of truth for what gets taught each semester. A syllabus typically contains topic lists, learning outcomes, and reading references — but it is a planning document, not a teaching resource. Converting that raw outline into a complete, structured learning experience (lecture notes, explanations, assessments, revision materials) is entirely manual work done by individual faculty members.

---

## The Problem

**College professors and educators spend significant time converting a syllabus into a complete, structured course with lectures, explanations, study materials, assessments, and revision resources.**

A typical course preparation workflow looks like this:

1. Parse the syllabus into individual topics (manual, error-prone).
2. Write lecture notes or slides for each topic (1–3 hours per topic).
3. Design assessments and quiz questions that map back to each topic (1–2 hours per topic).
4. Create revision materials, question banks, and practice sets (additional hours per course).
5. Repeat every semester, often from scratch, even for similar topics taught before.

For a course with 5 modules and 4 topics each, this process can consume **60–100+ hours per course per semester** — time that faculty cannot spend on research, mentoring, or improving pedagogical methods.

---

## Who is Affected

### Primary persona — College Professors and Instructors
Faculty at universities and colleges who are responsible for designing and delivering courses. They typically:
- Manage 2–4 courses simultaneously, each with 20–80 students.
- Have limited time between semesters to prepare new or updated course material.
- Lack dedicated instructional-design support staff.
- Must maintain consistent content quality across all topics, even for courses they inherited or are teaching for the first time.

### Secondary persona — Students
Students who depend on structured learning content, consistent explanations, and adequate assessment practice to prepare for exams. When faculty do not have time to produce comprehensive materials, students receive:
- Incomplete or inconsistent topic coverage.
- Insufficient practice questions or quizzes.
- No structured revision materials aligned to the course syllabus.

---

## Why It Matters

| Impact | Detail |
|---|---|
| **Time cost to faculty** | 60–100+ hours of manual content creation per course per semester |
| **Inconsistency** | Content quality varies by how much preparation time a professor has, not by topic importance |
| **Student outcomes** | Students without structured study materials are more likely to under-prepare for assessments |
| **Scalability** | As class sizes grow and online/hybrid delivery expands, the gap between syllabus and learning content widens |
| **Missed feedback loop** | Without a quiz or assessment per topic, faculty cannot identify which topics students struggle with until after the exam |

---

## Why Existing Solutions Fall Short

| Existing approach | Limitation |
|---|---|
| **Manual preparation** | Extremely time-consuming; quality depends on faculty bandwidth |
| **Generic LMS templates** (Moodle, Canvas) | Provide structure but not content — faculty still write everything |
| **Generic AI tools** (ChatGPT, etc.) | Useful for one-off text, but require prompt engineering per topic, produce no structured hierarchy, and don't persist output to a database or connect to an LMS workflow |
| **Publisher course packs** | Locked to a specific textbook; not customisable; expensive; lag behind syllabus changes |
| **Outsourced content development** | Costly, slow (weeks to months), and requires significant back-and-forth with instructional designers |

None of these approaches solve the core problem: **given a syllabus, automatically produce a complete, browsable, per-topic learning experience** — structured, consistent, immediately usable — without requiring significant manual effort from the professor.

---

## Why This Problem Matters Now

- **Generative AI** has reached a quality threshold where structured, educational content can be generated reliably from a prompt — but there is no purpose-built tool that integrates this into an educator's workflow.
- **Online and hybrid learning** has increased the demand for digital course materials, raising the bar for what "adequate course preparation" means.
- **Faculty burnout** is well-documented in post-pandemic academia — reducing the administrative burden of content creation directly improves faculty wellbeing and teaching quality.
- **Students increasingly expect** interactive, on-demand learning resources rather than PDF slides — a gap that AI-generated structured content can begin to close.
