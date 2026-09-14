"""
Tests for GET /health endpoint.

Run with:
    pytest src/backend/tests/ -v
"""
import pytest
from fastapi.testclient import TestClient

from src.backend.app.main import app

client = TestClient(app)


class TestHealthEndpoint:
    """Unit tests for the /health liveness endpoint."""

    def test_health_returns_200(self):
        """The endpoint must respond with HTTP 200."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_status_is_ok(self):
        """The 'status' field must equal 'ok'."""
        response = client.get("/health")
        body = response.json()
        assert body["status"] == "ok"

    def test_health_service_name(self):
        """The 'service' field must equal the configured app name."""
        response = client.get("/health")
        body = response.json()
        assert body["service"] == "CourseGenie AI"

    def test_health_response_shape(self):
        """Response body must contain exactly the documented keys."""
        response = client.get("/health")
        body = response.json()
        assert set(body.keys()) == {"status", "service"}

    def test_health_content_type_is_json(self):
        """Response must be JSON."""
        response = client.get("/health")
        assert "application/json" in response.headers["content-type"]
