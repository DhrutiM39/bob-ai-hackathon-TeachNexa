"""
ORM models for CourseGenie AI.

Hierarchy:
  users
    └─ courses
         └─ modules
              └─ topics
                   ├─ content
                   └─ quizzes
                        └─ questions
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import relationship

from .connection import Base


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# users
# ---------------------------------------------------------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="student")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)

    # relationships
    courses = relationship("Course", back_populates="owner", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"


# ---------------------------------------------------------------------------
# courses
# ---------------------------------------------------------------------------
class Course(Base):
    __tablename__ = "courses"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    syllabus_text = Column(Text, nullable=True)
    owner_id = Column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    # relationships
    owner = relationship("User", back_populates="courses")
    modules = relationship("Module", back_populates="course", cascade="all, delete-orphan")
    revision_content = relationship(
        "Content",
        back_populates="course",
        cascade="all, delete-orphan",
        foreign_keys="Content.course_id",
    )

    __table_args__ = (
        Index("ix_courses_owner_id", "owner_id"),
    )

    def __repr__(self) -> str:
        return f"<Course id={self.id} title={self.title!r}>"


# ---------------------------------------------------------------------------
# modules
# ---------------------------------------------------------------------------
class Module(Base):
    __tablename__ = "modules"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, nullable=False)
    course_id = Column(
        Uuid,
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
    )
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    order_no = Column(Integer, nullable=False, default=0)

    # relationships
    course = relationship("Course", back_populates="modules")
    topics = relationship("Topic", back_populates="module", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_modules_course_id", "course_id"),
    )

    def __repr__(self) -> str:
        return f"<Module id={self.id} title={self.title!r}>"


# ---------------------------------------------------------------------------
# topics
# ---------------------------------------------------------------------------
class Topic(Base):
    __tablename__ = "topics"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, nullable=False)
    module_id = Column(
        Uuid,
        ForeignKey("modules.id", ondelete="CASCADE"),
        nullable=False,
    )
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    order_no = Column(Integer, nullable=False, default=0)

    # relationships
    module = relationship("Module", back_populates="topics")
    content_items = relationship("Content", back_populates="topic", cascade="all, delete-orphan")
    quizzes = relationship("Quiz", back_populates="topic", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_topics_module_id", "module_id"),
    )

    def __repr__(self) -> str:
        return f"<Topic id={self.id} title={self.title!r}>"


# ---------------------------------------------------------------------------
# content
# ---------------------------------------------------------------------------
class Content(Base):
    __tablename__ = "content"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, nullable=False)
    # topic_id is nullable — revision rows are anchored by course_id instead.
    topic_id = Column(
        Uuid,
        ForeignKey("topics.id", ondelete="CASCADE"),
        nullable=True,
    )
    # course_id is set only for course-level content (content_type="revision").
    # Nullable so existing topic-level rows are unaffected.
    course_id = Column(
        Uuid,
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=True,
    )
    content_type = Column(String(100), nullable=False)  # e.g. "lecture", "revision"
    title = Column(String(500), nullable=False)
    body = Column(Text, nullable=True)
    model_name = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)

    # relationships
    topic = relationship("Topic", back_populates="content_items")
    course = relationship("Course", back_populates="revision_content")

    __table_args__ = (
        Index("ix_content_topic_id", "topic_id"),
        Index("ix_content_course_id", "course_id"),
        # At most one generated item of each type per topic.
        # NULL topic_id values (revision rows) are excluded by SQL-standard NULL
        # uniqueness rules on both SQLite and PostgreSQL.
        Index("uq_content_topic_type", "topic_id", "content_type", unique=True),
        # At most one revision per course.
        Index("uq_content_course_type", "course_id", "content_type", unique=True),
    )

    def __repr__(self) -> str:
        return f"<Content id={self.id} title={self.title!r}>"


# ---------------------------------------------------------------------------
# quizzes
# ---------------------------------------------------------------------------
class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, nullable=False)
    topic_id = Column(
        Uuid,
        ForeignKey("topics.id", ondelete="CASCADE"),
        nullable=False,
    )
    title = Column(String(500), nullable=False)
    instructions = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)

    # relationships
    topic = relationship("Topic", back_populates="quizzes")
    questions = relationship("Question", back_populates="quiz", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_quizzes_topic_id", "topic_id"),
    )

    def __repr__(self) -> str:
        return f"<Quiz id={self.id} title={self.title!r}>"


# ---------------------------------------------------------------------------
# questions
# ---------------------------------------------------------------------------
class Question(Base):
    __tablename__ = "questions"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, nullable=False)
    quiz_id = Column(
        Uuid,
        ForeignKey("quizzes.id", ondelete="CASCADE"),
        nullable=False,
    )
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50), nullable=False)  # e.g. "mcq", "true_false", "short_answer"
    # JSON works on all dialects (PostgreSQL stores it as JSONB via the migration).
    options = Column(JSON, nullable=True)               # list of answer choices for MCQ
    correct_answer = Column(Text, nullable=True)
    explanation = Column(Text, nullable=True)
    marks = Column(Integer, nullable=False, default=1)

    # relationships
    quiz = relationship("Quiz", back_populates="questions")

    __table_args__ = (
        Index("ix_questions_quiz_id", "quiz_id"),
    )

    def __repr__(self) -> str:
        return f"<Question id={self.id} type={self.question_type!r}>"
