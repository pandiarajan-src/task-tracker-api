import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, get_db
from main import app

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def client():
    Base.metadata.create_all(bind=engine)
    yield TestClient(app)
    Base.metadata.drop_all(bind=engine)


def test_get_root_returns_correct_message(client):
    """Should return API information when accessing root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Task Tracker API"
    assert "version" in data


def test_get_tasks_returns_empty_list_when_no_tasks(client):
    """Should return empty list when no tasks exist."""
    response = client.get("/tasks")
    assert response.status_code == 200
    assert response.json() == []


def test_create_task_success_with_valid_data(client):
    """Should create task successfully when valid data is provided."""
    task_data = {
        "title": "Test Task",
        "description": "Test Description",
        "completed": False
    }
    response = client.post("/tasks", json=task_data)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == task_data["title"]
    assert data["description"] == task_data["description"]
    assert data["completed"] == task_data["completed"]
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_task_fails_with_missing_title(client):
    """Should fail to create task when title is missing."""
    task_data = {
        "description": "Test Description",
        "completed": False
    }
    response = client.post("/tasks", json=task_data)
    assert response.status_code == 422


def test_get_task_success_with_existing_id(client):
    """Should return task successfully when valid ID is provided."""
    # First create a task
    task_data = {"title": "Test Task", "description": "Test Description"}
    create_response = client.post("/tasks", json=task_data)
    task_id = create_response.json()["id"]
    
    # Then get it
    response = client.get(f"/tasks/{task_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task_id
    assert data["title"] == task_data["title"]


def test_get_task_fails_with_nonexistent_id(client):
    """Should return 404 when task ID does not exist."""
    response = client.get("/tasks/999")
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


def test_update_task_success_with_valid_data(client):
    """Should update task successfully when valid data is provided."""
    # First create a task
    task_data = {"title": "Original Title", "description": "Original Description"}
    create_response = client.post("/tasks", json=task_data)
    task_id = create_response.json()["id"]
    
    # Then update it
    update_data = {"title": "Updated Title", "completed": True}
    response = client.put(f"/tasks/{task_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == update_data["title"]
    assert data["completed"] == update_data["completed"]
    assert data["description"] == task_data["description"]  # Should remain unchanged


def test_update_task_fails_with_nonexistent_id(client):
    """Should return 404 when trying to update nonexistent task."""
    update_data = {"title": "Updated Title"}
    response = client.put("/tasks/999", json=update_data)
    assert response.status_code == 404


def test_delete_task_success_with_existing_id(client):
    """Should delete task successfully when valid ID is provided."""
    # First create a task
    task_data = {"title": "Task to Delete"}
    create_response = client.post("/tasks", json=task_data)
    task_id = create_response.json()["id"]
    
    # Then delete it
    response = client.delete(f"/tasks/{task_id}")
    assert response.status_code == 200
    data = response.json()
    assert "successfully deleted" in data["message"].lower()
    
    # Verify it's gone
    get_response = client.get(f"/tasks/{task_id}")
    assert get_response.status_code == 404


def test_delete_task_fails_with_nonexistent_id(client):
    """Should return 404 when trying to delete nonexistent task."""
    response = client.delete("/tasks/999")
    assert response.status_code == 404


def test_get_tasks_returns_created_tasks(client):
    """Should return all created tasks when getting tasks list."""
    # Create multiple tasks
    tasks = [
        {"title": "Task 1", "description": "Description 1"},
        {"title": "Task 2", "description": "Description 2"},
        {"title": "Task 3", "completed": True}
    ]
    
    for task in tasks:
        client.post("/tasks", json=task)
    
    # Get all tasks
    response = client.get("/tasks")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert all("id" in task for task in data)
    assert all("title" in task for task in data)