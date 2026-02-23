"""
Comprehensive test suite for Task Tracker API.
Tests all CRUD endpoints with happy path and error cases.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.database import Base, get_db
from app.main import app

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Override the database dependency
app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test and drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


# Root endpoint test
def test_read_root_returns_api_info():
    """Test root endpoint returns application information."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == settings.app_name
    assert data["version"] == settings.app_version
    assert "api_prefix" in data


# CREATE tests
def test_create_task_success_returns_created_task():
    """Test creating a task successfully returns 201 with task data."""
    task_data = {"title": "Test Task", "description": "Test Description", "completed": False}
    response = client.post(f"{settings.api_v1_prefix}/tasks", json=task_data)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == task_data["title"]
    assert data["description"] == task_data["description"]
    assert data["completed"] == task_data["completed"]
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_task_with_minimal_data_succeeds():
    """Test creating a task with only required fields succeeds."""
    task_data = {"title": "Minimal Task"}
    response = client.post(f"{settings.api_v1_prefix}/tasks", json=task_data)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Minimal Task"
    assert data["description"] is None
    assert data["completed"] is False


def test_create_task_without_title_fails():
    """Test creating a task without title returns 422."""
    task_data = {"description": "No title"}
    response = client.post(f"{settings.api_v1_prefix}/tasks", json=task_data)
    assert response.status_code == 422


# READ tests
def test_get_tasks_returns_empty_list_initially():
    """Test GET /tasks returns empty list when no tasks exist."""
    response = client.get(f"{settings.api_v1_prefix}/tasks")
    assert response.status_code == 200
    assert response.json() == []


def test_get_tasks_returns_all_tasks():
    """Test GET /tasks returns all created tasks."""
    # Create two tasks
    client.post(f"{settings.api_v1_prefix}/tasks", json={"title": "Task 1"})
    client.post(f"{settings.api_v1_prefix}/tasks", json={"title": "Task 2"})

    response = client.get(f"{settings.api_v1_prefix}/tasks")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["title"] == "Task 1"
    assert data[1]["title"] == "Task 2"


def test_get_task_by_id_returns_specific_task():
    """Test GET /tasks/{id} returns the correct task."""
    # Create a task
    create_response = client.post(
        f"{settings.api_v1_prefix}/tasks", json={"title": "Specific Task"}
    )
    task_id = create_response.json()["id"]

    # Get the task
    response = client.get(f"{settings.api_v1_prefix}/tasks/{task_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task_id
    assert data["title"] == "Specific Task"


def test_get_nonexistent_task_returns_404():
    """Test GET /tasks/{id} with invalid id returns 404."""
    response = client.get(f"{settings.api_v1_prefix}/tasks/999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


# UPDATE tests
def test_update_task_changes_fields_successfully():
    """Test PUT /tasks/{id} updates task fields."""
    # Create a task
    create_response = client.post(
        f"{settings.api_v1_prefix}/tasks", json={"title": "Original Title", "completed": False}
    )
    task_id = create_response.json()["id"]

    # Update the task
    update_data = {"title": "Updated Title", "completed": True}
    response = client.put(f"{settings.api_v1_prefix}/tasks/{task_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["completed"] is True


def test_update_task_partial_update_works():
    """Test partial update only changes specified fields."""
    # Create a task
    create_response = client.post(
        f"{settings.api_v1_prefix}/tasks",
        json={"title": "Original", "description": "Original Desc"},
    )
    task_id = create_response.json()["id"]

    # Update only completed field
    response = client.put(f"{settings.api_v1_prefix}/tasks/{task_id}", json={"completed": True})
    data = response.json()
    assert data["title"] == "Original"
    assert data["description"] == "Original Desc"
    assert data["completed"] is True


def test_update_nonexistent_task_returns_404():
    """Test updating non-existent task returns 404."""
    response = client.put(f"{settings.api_v1_prefix}/tasks/999", json={"title": "Updated"})
    assert response.status_code == 404


# DELETE tests
def test_delete_task_removes_task_successfully():
    """Test DELETE /tasks/{id} removes the task."""
    # Create a task
    create_response = client.post(f"{settings.api_v1_prefix}/tasks", json={"title": "To Delete"})
    task_id = create_response.json()["id"]

    # Delete the task
    response = client.delete(f"{settings.api_v1_prefix}/tasks/{task_id}")
    assert response.status_code == 200
    assert "successfully deleted" in response.json()["message"]

    # Verify task is deleted
    get_response = client.get(f"{settings.api_v1_prefix}/tasks/{task_id}")
    assert get_response.status_code == 404


def test_delete_nonexistent_task_returns_404():
    """Test deleting non-existent task returns 404."""
    response = client.delete(f"{settings.api_v1_prefix}/tasks/999")
    assert response.status_code == 404
