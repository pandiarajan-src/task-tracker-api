"""
Integration tests for the task priority system.
Simple, focused tests that prove the priority functionality works.
"""
import pytest
import json
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.database import Base, get_db
from app.main import app
from app.rate_limiter import limiter

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_priority.db"
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


@pytest.fixture(autouse=True, scope="function")
def setup():
    """Setup and teardown for each test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_create_task_with_high_priority():
    """Test creating a task with high priority."""
    task_data = {
        "title": "Urgent Task",
        "description": "High priority task",
        "priority": "high"
    }
    response = client.post(f"{settings.api_v1_prefix}/tasks", json=task_data)
    assert response.status_code == 201
    data = response.json()
    assert data["priority"] == "high"
    assert data["title"] == "Urgent Task"


def test_create_task_defaults_to_medium_priority():
    """Test task defaults to medium priority when not specified."""
    task_data = {"title": "Default Priority Task"}
    response = client.post(f"{settings.api_v1_prefix}/tasks", json=task_data)
    assert response.status_code == 201
    data = response.json()
    assert data["priority"] == "medium"


def test_filter_tasks_by_priority():
    """Test filtering tasks by priority."""
    # Create tasks
    tasks = [
        {"title": "High 1", "priority": "high"},
        {"title": "Low 1", "priority": "low"},
        {"title": "High 2", "priority": "high"},
    ]
    
    for task in tasks:
        response = client.post(f"{settings.api_v1_prefix}/tasks", json=task)
        assert response.status_code == 201
    
    # Filter high priority
    response = client.get(f"{settings.api_v1_prefix}/tasks?priority=high")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    for task in data:
        assert task["priority"] == "high"


def test_tasks_are_sorted_by_priority():
    """Test that tasks are returned sorted by priority."""
    # Create tasks in mixed order
    tasks = [
        {"title": "Low Priority", "priority": "low"},
        {"title": "High Priority", "priority": "high"},
        {"title": "Medium Priority", "priority": "medium"},
    ]
    
    for task in tasks:
        response = client.post(f"{settings.api_v1_prefix}/tasks", json=task)
        assert response.status_code == 201
    
    # Get all tasks 
    response = client.get(f"{settings.api_v1_prefix}/tasks")
    assert response.status_code == 200
    data = response.json()
    
    # Check order: high -> medium -> low
    priorities = [task["priority"] for task in data]
    assert priorities == ["high", "medium", "low"]


def test_invalid_priority_rejected():
    """Test that invalid priority values are rejected."""
    task_data = {
        "title": "Invalid Priority Task",
        "priority": "critical"  # Not a valid priority
    }
    response = client.post(f"{settings.api_v1_prefix}/tasks", json=task_data)
    assert response.status_code == 422


def test_update_task_priority():
    """Test updating a task's priority."""
    # Create task
    task_data = {"title": "Update Test", "priority": "low"}
    response = client.post(f"{settings.api_v1_prefix}/tasks", json=task_data)
    task_id = response.json()["id"]
    
    # Update priority
    update_data = {"priority": "high"}
    response = client.put(f"{settings.api_v1_prefix}/tasks/{task_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["priority"] == "high"