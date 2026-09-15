"""content: add course_id FK, make topic_id nullable, add unique indexes

Revision ID: 0002_content_course_id
Revises: 0001_initial
Create Date: 2025-01-02 00:00:00.000000

Changes:
  1. content.topic_id: NOT NULL → NULL  (revision rows have no topic anchor)
  2. content.course_id: new nullable UUID FK → courses.id ON DELETE CASCADE
  3. ix_content_course_id: new index on content.course_id
  4. uq_content_topic_type: unique index on (topic_id, content_type)
     — at most one generated lecture per topic
  5. uq_content_course_type: unique index on (course_id, content_type)
     — at most one revision per course
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0002_content_course_id"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Make topic_id nullable
    op.alter_column("content", "topic_id", existing_type=UUID(as_uuid=True), nullable=True)

    # 2. Add course_id column (nullable FK)
    op.add_column(
        "content",
        sa.Column(
            "course_id",
            UUID(as_uuid=True),
            sa.ForeignKey("courses.id", ondelete="CASCADE"),
            nullable=True,
        ),
    )

    # 3. Index on course_id
    op.create_index("ix_content_course_id", "content", ["course_id"])

    # 4. Unique index: at most one content row of a given type per topic
    #    (NULL topic_id values are excluded from uniqueness by SQL standard —
    #     this correctly ignores revision rows whose topic_id IS NULL)
    op.create_index(
        "uq_content_topic_type",
        "content",
        ["topic_id", "content_type"],
        unique=True,
        postgresql_where=sa.text("topic_id IS NOT NULL"),
    )

    # 5. Unique index: at most one revision row per course
    op.create_index(
        "uq_content_course_type",
        "content",
        ["course_id", "content_type"],
        unique=True,
        postgresql_where=sa.text("course_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_content_course_type", table_name="content")
    op.drop_index("uq_content_topic_type", table_name="content")
    op.drop_index("ix_content_course_id", table_name="content")
    op.drop_column("content", "course_id")
    op.alter_column("content", "topic_id", existing_type=UUID(as_uuid=True), nullable=False)
