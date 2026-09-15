"""schemas package — re-exports all Pydantic request/response models."""

# Health schemas
from .health import HealthResponse

# Syllabus schemas
from .syllabus import SyllabusRequest, SyllabusResponse

# Course generation schemas (POST /api/v1/courses/generate)
from .generate import (
    GenerateCourseRequest,
    GenerateCourseResponse,
    ModuleOut,
    TopicOut,
    ErrorResponse,
)

# Course retrieval + edit schemas
from .courses import (
    CourseListItem,
    CourseDetail,
    CoursesListResponse,
    CourseUpdate,
    ModuleUpdate,
    TopicUpdate,
)

# Topic content / quiz / revision schemas
from .topics import (
    KeyConcept,
    ContentExample,
    TopicContentResponse,
    QuizOption,
    QuizQuestion,
    QuizResponse,
    RevisionQuestion,
    RevisionResponse,
)

__all__ = [
    "HealthResponse",
    "SyllabusRequest",
    "SyllabusResponse",
    "GenerateCourseRequest",
    "GenerateCourseResponse",
    "ModuleOut",
    "TopicOut",
    "ErrorResponse",
    "CourseListItem",
    "CourseDetail",
    "CoursesListResponse",
    "CourseUpdate",
    "ModuleUpdate",
    "TopicUpdate",
    "KeyConcept",
    "ContentExample",
    "TopicContentResponse",
    "QuizOption",
    "QuizQuestion",
    "QuizResponse",
    "RevisionQuestion",
    "RevisionResponse",
]
