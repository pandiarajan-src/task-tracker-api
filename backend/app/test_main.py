"""
Comprehensive test suite for Task Tracker API.
Tests all CRUD endpoints with happy path and error cases.
"""

import os

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")
os.environ.setdefault("AUTH_REQUIRED", "false")
os.environ.setdefault("ENFORCE_HTTPS", "false")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.database import Base, get_db
from app.main import app
from app.rate_limiter import limiter

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


# Create test client
client = TestClient(app)


@pytest.fixture(scope="function", autouse=True)
def override_db_dependency():
    """Ensure each test uses the module's test database override."""
    app.dependency_overrides[get_db] = override_get_db
    if hasattr(limiter, "enabled"):
        limiter.enabled = False
    yield
    if hasattr(limiter, "enabled"):
        limiter.enabled = True
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture(scope="function", autouse=True)
def setup_database():
    """Create tables before each test and drop after."""
    # Always start with clean slate
    Base.metadata.drop_all(bind=engine)
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
    
    # Tasks are sorted by priority (high->medium->low) then by created_at desc
    # Since both tasks have the same default priority (medium), 
    # the more recent task (Task 2) should come first
    assert data[0]["title"] == "Task 2"
    assert data[1]["title"] == "Task 1"


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


# Priority functionality tests
def test_create_task_with_priority_success():
    """Should create task with specified priority successfully."""
    task_data = {
        "title": "High Priority Task",
        "description": "Important task",
        "priority": "high"
    }
    response = client.post(f"{settings.api_v1_prefix}/tasks", json=task_data)
    assert response.status_code == 201
    data = response.json()
    assert data["priority"] == "high"
    assert data["title"] == task_data["title"]


def test_create_task_with_default_priority():
    """Should create task with default medium priority when not specified."""
    task_data = {"title": "Default Priority Task"}
    response = client.post(f"{settings.api_v1_prefix}/tasks", json=task_data)
    assert response.status_code == 201
    data = response.json()
    assert data["priority"] == "medium"  # Default priority


def test_filter_tasks_by_priority_high():
    """Should filter tasks by high priority."""
    # Create tasks with different priorities
    tasks_data = [
        {"title": "Low Priority", "priority": "low"},
        {"title": "High Priority 1", "priority": "high"},
        {"title": "Medium Priority", "priority": "medium"}, 
        {"title": "High Priority 2", "priority": "high"}
    ]
    
    for task in tasks_data:
        client.post(f"{settings.api_v1_prefix}/tasks", json=task)
    
    # Filter by high priority
    response = client.get(f"{settings.api_v1_prefix}/tasks?priority=high")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(task["priority"] == "high" for task in data)


def test_filter_tasks_by_priority_medium():
    """Should filter tasks by medium priority.""" 
    # Create tasks with different priorities
    tasks_data = [
        {"title": "Low Priority", "priority": "low"},
        {"title": "Medium Priority 1", "priority": "medium"},
        {"title": "High Priority", "priority": "high"},
        {"title": "Medium Priority 2", "priority": "medium"}
    ]
    
    for task in tasks_data:
        client.post(f"{settings.api_v1_prefix}/tasks", json=task)
    
    # Filter by medium priority
    response = client.get(f"{settings.api_v1_prefix}/tasks?priority=medium")  
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2  # At least the 2 we created
    assert all(task["priority"] == "medium" for task in data)


def test_invalid_priority_value_fails():
    """Should fail when invalid priority is provided."""
    task_data = {
        "title": "Invalid Priority Task",
        "priority": "urgent"  # Invalid priority
    }
    response = client.post(f"{settings.api_v1_prefix}/tasks", json=task_data)
    assert response.status_code == 422


def test_tasks_sorted_by_priority():
    """Should return tasks sorted by priority (high -> medium -> low)."""
    # Create tasks with different priorities 
    tasks_data = [
        {"title": "Low Priority Task", "priority": "low"},
        {"title": "High Priority Task", "priority": "high"},
        {"title": "Medium Priority Task", "priority": "medium"},
        {"title": "Another High Priority", "priority": "high"}
    ]
    
    for task in tasks_data:
        client.post(f"{settings.api_v1_prefix}/tasks", json=task)
    
    # Get all tasks
    response = client.get(f"{settings.api_v1_prefix}/tasks")
    assert response.status_code == 200
    data = response.json()
    
    # Check that high priority tasks come first
    priorities = [task["priority"] for task in data]
    
    # Find positions of different priorities
    high_positions = [i for i, p in enumerate(priorities) if p == "high"]
    medium_positions = [i for i, p in enumerate(priorities) if p == "medium"] 
    low_positions = [i for i, p in enumerate(priorities) if p == "low"]
    
    # High priority should come before medium and low
    if high_positions and medium_positions:
        assert max(high_positions) < min(medium_positions)
    if medium_positions and low_positions:
        assert max(medium_positions) < min(low_positions)


def test_update_task_priority():
    """Should update task priority successfully."""
    # Create a task 
    task_data = {"title": "Update Priority Test", "priority": "low"}
    create_response = client.post(f"{settings.api_v1_prefix}/tasks", json=task_data)
    task_id = create_response.json()["id"]
    
    # Update priority to high
    update_data = {"priority": "high"}
    response = client.put(f"{settings.api_v1_prefix}/tasks/{task_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["priority"] == "high"
    assert data["title"] == task_data["title"]  # Other fields unchanged


def test_filter_tasks_by_priority_low():
    """Should filter tasks by low priority."""
    # Create tasks with different priorities
    tasks_data = [
        {"title": "Low Priority 1", "priority": "low"},
        {"title": "Medium Priority", "priority": "medium"},
        {"title": "High Priority", "priority": "high"},
        {"title": "Low Priority 2", "priority": "low"}
    ]
    
    for task in tasks_data:
        client.post(f"{settings.api_v1_prefix}/tasks", json=task)
    
    # Filter by low priority
    response = client.get(f"{settings.api_v1_prefix}/tasks?priority=low")  
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(task["priority"] == "low" for task in data)
