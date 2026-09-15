"""
Tests for POST /api/v1/syllabus endpoint.

Run with:
    pytest src/backend/tests/ -v
"""
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)

ENDPOINT = "/api/v1/syllabus"

VALID_PAYLOAD = {
    "course_name": "Introduction to Artificial Intelligence",
    "syllabus_text": (
        "Module 1: Introduction to AI\n"
        "Module 2: Search Algorithms\n"
        "Module 3: Machine Learning Basics"
    ),
}


class TestSyllabusValidSubmission:
    """Happy-path tests — valid input should return 201 with full response."""

    def test_valid_submission_returns_201(self):
        response = client.post(ENDPOINT, json=VALID_PAYLOAD)
        assert response.status_code == 201

    def test_valid_submission_response_structure(self):
        """Response must contain all documented fields."""
        response = client.post(ENDPOINT, json=VALID_PAYLOAD)
        body = response.json()
        required_keys = {"status", "syllabus_id", "course_name", "syllabus_text",
                         "character_count", "message"}
        assert required_keys == set(body.keys())

    def test_valid_submission_status_is_accepted(self):
        response = client.post(ENDPOINT, json=VALID_PAYLOAD)
        assert response.json()["status"] == "accepted"

    def test_valid_submission_course_name_echoed(self):
        response = client.post(ENDPOINT, json=VALID_PAYLOAD)
        assert response.json()["course_name"] == VALID_PAYLOAD["course_name"]

    def test_valid_submission_syllabus_id_format(self):
        """syllabus_id must follow the cg-<hash>-<uid> pattern."""
        response = client.post(ENDPOINT, json=VALID_PAYLOAD)
        syllabus_id = response.json()["syllabus_id"]
        parts = syllabus_id.split("-")
        assert parts[0] == "cg", f"ID prefix wrong: {syllabus_id}"
        assert len(parts) == 3, f"ID segment count wrong: {syllabus_id}"

    def test_valid_submission_character_count_correct(self):
        response = client.post(ENDPOINT, json=VALID_PAYLOAD)
        body = response.json()
        assert body["character_count"] == len(body["syllabus_text"])

    def test_valid_submission_syllabus_text_normalised(self):
        """Leading/trailing whitespace in syllabus_text must be stripped."""
        padded = dict(VALID_PAYLOAD)
        padded["syllabus_text"] = "  " + VALID_PAYLOAD["syllabus_text"] + "  "
        response = client.post(ENDPOINT, json=padded)
        assert response.status_code == 201
        assert not response.json()["syllabus_text"].startswith(" ")
        assert not response.json()["syllabus_text"].endswith(" ")

    def test_unique_ids_per_submission(self):
        """Two identical submissions must produce distinct syllabus_ids."""
        r1 = client.post(ENDPOINT, json=VALID_PAYLOAD)
        r2 = client.post(ENDPOINT, json=VALID_PAYLOAD)
        assert r1.json()["syllabus_id"] != r2.json()["syllabus_id"]


class TestSyllabusValidationErrors:
    """Validation-failure tests — bad input must return 422 with detail."""

    def test_empty_course_name_returns_422(self):
        payload = {**VALID_PAYLOAD, "course_name": ""}
        response = client.post(ENDPOINT, json=payload)
        assert response.status_code == 422

    def test_blank_course_name_returns_422(self):
        """Whitespace-only course name must be rejected."""
        payload = {**VALID_PAYLOAD, "course_name": "   "}
        response = client.post(ENDPOINT, json=payload)
        assert response.status_code == 422

    def test_empty_syllabus_text_returns_422(self):
        payload = {**VALID_PAYLOAD, "syllabus_text": ""}
        response = client.post(ENDPOINT, json=payload)
        assert response.status_code == 422

    def test_blank_syllabus_text_returns_422(self):
        """Whitespace-only syllabus_text must be rejected."""
        payload = {**VALID_PAYLOAD, "syllabus_text": "   "}
        response = client.post(ENDPOINT, json=payload)
        assert response.status_code == 422

    def test_too_short_syllabus_returns_422(self):
        """Syllabus under 20 chars must be rejected with a helpful message."""
        payload = {**VALID_PAYLOAD, "syllabus_text": "Too short"}
        response = client.post(ENDPOINT, json=payload)
        assert response.status_code == 422
        error_detail = str(response.json())
        assert "too short" in error_detail.lower() or "minimum" in error_detail.lower()

    def test_missing_course_name_returns_422(self):
        """Omitting course_name entirely must return 422."""
        payload = {"syllabus_text": VALID_PAYLOAD["syllabus_text"]}
        response = client.post(ENDPOINT, json=payload)
        assert response.status_code == 422

    def test_missing_syllabus_text_returns_422(self):
        """Omitting syllabus_text entirely must return 422."""
        payload = {"course_name": VALID_PAYLOAD["course_name"]}
        response = client.post(ENDPOINT, json=payload)
        assert response.status_code == 422


class TestSyllabusMalformedRequest:
    """Malformed / wrong content-type requests."""

    def test_empty_body_returns_422(self):
        response = client.post(ENDPOINT, json={})
        assert response.status_code == 422

    def test_non_json_body_returns_422(self):
        response = client.post(
            ENDPOINT,
            content=b"this is not json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422
