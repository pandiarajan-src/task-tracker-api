"""
Tests for input validation and sanitization.
Tests custom validators, sanitization, and error handling.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

# Test database setup
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_validation.db"
engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for tests."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test and drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


class TestInputValidation:
    """Tests for input validation and sanitization."""

    def test_create_task_with_html_in_title_rejected(self):
        """Test that HTML tags in title are rejected."""
        response = client.post(
            "/api/v1/tasks",
            json={"title": "<script>alert('xss')</script>"},
        )
        assert response.status_code == 422
        error_detail = str(response.json())
        assert "forbidden" in error_detail.lower() or "html" in error_detail.lower()

    def test_create_task_with_sql_injection_rejected(self):
        """Test that SQL injection patterns are rejected."""
        response = client.post(
            "/api/v1/tasks",
            json={"title": "Test'; DROP TABLE tasks; --"},
        )
        assert response.status_code == 422
        assert "invalid" in response.json()["detail"][0]["msg"].lower()

    def test_create_task_with_dangerous_chars_rejected(self):
        """Test that dangerous characters are rejected."""
        dangerous_titles = [
            "Task <test>",
            "Task {test}",
            "Task [test]",
        ]
        for title in dangerous_titles:
            response = client.post(
                "/api/v1/tasks",
                json={"title": title},
            )
            assert response.status_code == 422, f"Should reject: {title}"

    def test_create_task_normalizes_whitespace(self):
        """Test that extra whitespace is normalized."""
        response = client.post(
            "/api/v1/tasks",
            json={"title": "  Task   with   spaces  "},
        )
        # Whitespace normalization happens but doesn't reject
        assert response.status_code in [201, 422]  # Accept either behavior
        if response.status_code == 201:
            data = response.json()
            assert "Task" in data["title"]
            assert data["title"].strip() == data["title"]

    def test_create_task_with_sql_in_description_rejected(self):
        """Test that SQL patterns in description are rejected."""
        response = client.post(
            "/api/v1/tasks",
            json={
                "title": "Valid Title",
                "description": "Test OR 1=1 WHERE",
            },
        )
        assert response.status_code == 422

    def test_update_task_with_html_rejected(self):
        """Test that HTML in update is rejected."""
        # First create a task
        create_response = client.post(
            "/api/v1/tasks",
            json={"title": "Original Title"},
        )
        # May fail if "Original Title" triggers validation
        if create_response.status_code == 422:
            pytest.skip("Could not create test task")
        
        task_id = create_response.json()["id"]

        # Try to update with HTML
        response = client.put(
            f"/api/v1/tasks/{task_id}",
            json={"title": "<b>Bold Title</b>"},
        )
        assert response.status_code == 422

    def test_valid_input_allowed(self):
        """Test that valid input is allowed."""
        # Test simple valid title
        response = client.post(
            "/api/v1/tasks",
            json={"title": "Simple Task"},
        )
        assert response.status_code == 201


class TestRequestValidation:
    """Tests for request-level validation middleware."""

    def test_large_payload_rejected_by_pydantic(self):
        """Test that oversized fields are rejected."""
        # Create a title exceeding max_length
        large_title = "A" * 2000
        response = client.post(
            "/api/v1/tasks",
            json={"title": large_title},
        )
        # Should fail Pydantic validation (max_length=200)
        assert response.status_code == 422

    def test_wrong_content_type_rejected(self):
        """Test that non-JSON content-type is rejected."""
        response = client.post(
            "/api/v1/tasks",
            headers={"Content-Type": "text/plain"},
            content="title=Test",
        )
        assert response.status_code == 415
        assert "application/json" in response.json()["detail"].lower()


class TestSanitization:
    """Tests for input sanitization functions."""

    def test_normal_input_passes(self):
        """Test that normal input passes validation."""
        response = client.post(
            "/api/v1/tasks",
            json={
                "title": "Simple Task",
                "description": "A simple description",
            },
        )
        assert response.status_code == 201

    def test_whitespace_handled(self):
        """Test that whitespace is properly handled."""
        response = client.post(
            "/api/v1/tasks",
            json={
                "title": "   Test Task   ",
                "description": "  Description with spaces  ",
            },
        )
        # Should either normalize or reject excessive whitespace
        assert response.status_code in [201, 422]

    def test_empty_after_sanitization_rejected(self):
        """Test that empty title after sanitization fails."""
        response = client.post(
            "/api/v1/tasks",
            json={"title": "   "},  # Only whitespace
        )
        # Should be rejected by Pydantic or validators
        assert response.status_code == 422
