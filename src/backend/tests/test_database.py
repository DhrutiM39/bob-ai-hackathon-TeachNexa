"""
Database unit tests for CourseGenie AI.

Covers:
  - model creation (all 7 entities)
  - basic CRUD (create / read / update / delete)
  - foreign-key relationships
  - cascade deletes
  - unique constraints

Tests run against an in-memory SQLite database — no live PostgreSQL required.
See conftest.py for fixture setup.
"""

import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from backend.database.models import (
    Content,
    Course,
    Module,
    Question,
    Quiz,
    Topic,
    User,
)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def make_user(db, *, name="Alice", email=None, role="instructor"):
    email = email or f"user_{uuid.uuid4().hex[:6]}@example.com"
    user = User(id=uuid.uuid4(), name=name, email=email, role=role)
    db.add(user)
    db.flush()
    return user


def make_course(db, owner):
    course = Course(
        id=uuid.uuid4(),
        title="Introduction to Python",
        description="Learn Python basics",
        syllabus_text="Week 1: Variables, Week 2: Loops",
        owner_id=owner.id,
    )
    db.add(course)
    db.flush()
    return course


def make_module(db, course, *, order_no=1):
    module = Module(
        id=uuid.uuid4(),
        course_id=course.id,
        title="Module 1 — Fundamentals",
        order_no=order_no,
    )
    db.add(module)
    db.flush()
    return module


def make_topic(db, module, *, order_no=1):
    topic = Topic(
        id=uuid.uuid4(),
        module_id=module.id,
        title="Variables and Data Types",
        order_no=order_no,
    )
    db.add(topic)
    db.flush()
    return topic


def make_content(db, topic):
    content = Content(
        id=uuid.uuid4(),
        topic_id=topic.id,
        content_type="lecture",
        title="Lecture: Variables",
        body="In Python a variable is created the moment you assign a value.",
        model_name="ibm/granite-13b-instruct-v2",
    )
    db.add(content)
    db.flush()
    return content


def make_quiz(db, topic):
    quiz = Quiz(
        id=uuid.uuid4(),
        topic_id=topic.id,
        title="Quiz 1 — Variables",
        instructions="Answer all questions.",
    )
    db.add(quiz)
    db.flush()
    return quiz


def make_question(db, quiz):
    question = Question(
        id=uuid.uuid4(),
        quiz_id=quiz.id,
        question_text="What keyword is used to define a variable in Python?",
        question_type="mcq",
        options=["var", "let", "No keyword needed", "define"],
        correct_answer="No keyword needed",
        explanation="Python uses dynamic typing — no keyword is required.",
        marks=2,
    )
    db.add(question)
    db.flush()
    return question


# ─────────────────────────────────────────────────────────────────────────────
# Model creation tests
# ─────────────────────────────────────────────────────────────────────────────

class TestModelCreation:
    def test_create_user(self, db):
        user = make_user(db)
        assert user.id is not None
        assert user.email is not None

    def test_create_course(self, db):
        user = make_user(db)
        course = make_course(db, user)
        assert course.id is not None
        assert course.owner_id == user.id

    def test_create_module(self, db):
        user = make_user(db)
        course = make_course(db, user)
        module = make_module(db, course)
        assert module.id is not None
        assert module.course_id == course.id

    def test_create_topic(self, db):
        user = make_user(db)
        course = make_course(db, user)
        module = make_module(db, course)
        topic = make_topic(db, module)
        assert topic.id is not None
        assert topic.module_id == module.id

    def test_create_content(self, db):
        user = make_user(db)
        course = make_course(db, user)
        module = make_module(db, course)
        topic = make_topic(db, module)
        content = make_content(db, topic)
        assert content.id is not None
        assert content.topic_id == topic.id
        assert content.content_type == "lecture"

    def test_create_quiz(self, db):
        user = make_user(db)
        course = make_course(db, user)
        module = make_module(db, course)
        topic = make_topic(db, module)
        quiz = make_quiz(db, topic)
        assert quiz.id is not None
        assert quiz.topic_id == topic.id

    def test_create_question(self, db):
        user = make_user(db)
        course = make_course(db, user)
        module = make_module(db, course)
        topic = make_topic(db, module)
        quiz = make_quiz(db, topic)
        question = make_question(db, quiz)
        assert question.id is not None
        assert question.quiz_id == quiz.id
        assert question.marks == 2


# ─────────────────────────────────────────────────────────────────────────────
# CRUD tests
# ─────────────────────────────────────────────────────────────────────────────

class TestCRUD:
    def test_read_user(self, db):
        user = make_user(db, name="Bob", email="bob@example.com")
        found = db.query(User).filter_by(email="bob@example.com").first()
        assert found is not None
        assert found.name == "Bob"

    def test_update_course_title(self, db):
        user = make_user(db)
        course = make_course(db, user)
        course.title = "Advanced Python"
        db.flush()
        refreshed = db.query(Course).filter_by(id=course.id).first()
        assert refreshed.title == "Advanced Python"

    def test_delete_module(self, db):
        user = make_user(db)
        course = make_course(db, user)
        module = make_module(db, course)
        module_id = module.id
        db.delete(module)
        db.flush()
        assert db.query(Module).filter_by(id=module_id).first() is None

    def test_update_question_marks(self, db):
        user = make_user(db)
        course = make_course(db, user)
        module = make_module(db, course)
        topic = make_topic(db, module)
        quiz = make_quiz(db, topic)
        question = make_question(db, quiz)
        question.marks = 5
        db.flush()
        refreshed = db.query(Question).filter_by(id=question.id).first()
        assert refreshed.marks == 5


# ─────────────────────────────────────────────────────────────────────────────
# Relationship tests
# ─────────────────────────────────────────────────────────────────────────────

class TestRelationships:
    def test_user_has_courses(self, db):
        user = make_user(db)
        make_course(db, user)
        make_course(db, user)
        db.refresh(user)
        assert len(user.courses) == 2

    def test_course_has_modules(self, db):
        user = make_user(db)
        course = make_course(db, user)
        make_module(db, course, order_no=1)
        make_module(db, course, order_no=2)
        db.refresh(course)
        assert len(course.modules) == 2

    def test_module_has_topics(self, db):
        user = make_user(db)
        course = make_course(db, user)
        module = make_module(db, course)
        make_topic(db, module, order_no=1)
        make_topic(db, module, order_no=2)
        db.refresh(module)
        assert len(module.topics) == 2

    def test_topic_has_content_and_quizzes(self, db):
        user = make_user(db)
        course = make_course(db, user)
        module = make_module(db, course)
        topic = make_topic(db, module)
        make_content(db, topic)
        make_quiz(db, topic)
        db.refresh(topic)
        assert len(topic.content_items) == 1
        assert len(topic.quizzes) == 1

    def test_quiz_has_questions(self, db):
        user = make_user(db)
        course = make_course(db, user)
        module = make_module(db, course)
        topic = make_topic(db, module)
        quiz = make_quiz(db, topic)
        make_question(db, quiz)
        make_question(db, quiz)
        db.refresh(quiz)
        assert len(quiz.questions) == 2

    def test_full_hierarchy_navigation(self, db):
        """Walk the full chain: user -> course -> module -> topic -> quiz -> question."""
        user = make_user(db)
        course = make_course(db, user)
        module = make_module(db, course)
        topic = make_topic(db, module)
        quiz = make_quiz(db, topic)
        question = make_question(db, quiz)

        # Navigate from question back up to user
        loaded_q = db.query(Question).filter_by(id=question.id).first()
        assert loaded_q.quiz.topic.module.course.owner.id == user.id


# ─────────────────────────────────────────────────────────────────────────────
# Constraint tests
# ─────────────────────────────────────────────────────────────────────────────

class TestConstraints:
    def test_unique_email_constraint(self, db):
        make_user(db, email="unique@example.com")
        with pytest.raises((IntegrityError, Exception)):
            make_user(db, email="unique@example.com")
            db.flush()

    def test_course_requires_owner(self, db):
        """Attempting to create a course with a non-existent owner_id must fail."""
        course = Course(
            id=uuid.uuid4(),
            title="Orphan Course",
            owner_id=uuid.uuid4(),  # no such user
        )
        db.add(course)
        with pytest.raises(Exception):
            db.flush()

    def test_cascade_delete_course_deletes_modules(self, db):
        user = make_user(db)
        course = make_course(db, user)
        module = make_module(db, course)
        module_id = module.id

        db.delete(course)
        db.flush()

        # Module should be gone because of cascade="all, delete-orphan"
        assert db.query(Module).filter_by(id=module_id).first() is None
