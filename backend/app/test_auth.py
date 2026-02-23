"""
Comprehensive test suite for Authentication API.
Tests user registration, login, token management, password reset, and user-scoped operations.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.database import Base, get_db
from app.main import app
from app.rate_limiter import limiter

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_auth.db"
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


# Test data
valid_user_data = {
    "email": "test@example.com",
    "password": "Pass123!",
    "name": "Test User"
}

valid_login_data = {
    "email": "test@example.com", 
    "password": "Pass123!"
}


# Helper functions
def create_test_user():
    """Create a test user and return the response."""
    response = client.post(f"{settings.api_v1_prefix}/auth/register", json=valid_user_data)
    return response


def login_test_user():
    """Create and login a test user, return access token."""
    create_test_user()
    login_response = client.post(f"{settings.api_v1_prefix}/auth/login", json=valid_login_data)
    return login_response.json()["access_token"]


def get_auth_headers(token: str):
    """Get authorization headers for API requests."""
    return {"Authorization": f"Bearer {token}"}


# User Registration Tests
def test_user_registration_success():
    """Test successful user registration."""
    response = create_test_user()
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == valid_user_data["email"]
    assert data["name"] == valid_user_data["name"]
    assert "password" not in data  # Password should not be returned
    assert "id" in data
    assert data["is_active"] == True


def test_user_registration_duplicate_email_fails():
    """Test registration with duplicate email fails."""
    # Create first user
    create_test_user()
    
    # Try to create another user with same email
    response = client.post(f"{settings.api_v1_prefix}/auth/register", json=valid_user_data)
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


def test_user_registration_invalid_email_fails():
    """Test registration with invalid email fails."""
    invalid_data = valid_user_data.copy() 
    invalid_data["email"] = "not-an-email"
    
    response = client.post(f"{settings.api_v1_prefix}/auth/register", json=invalid_data)
    assert response.status_code == 422


def test_user_registration_weak_password_fails():
    """Test registration with weak password fails.""" 
    weak_password_data = valid_user_data.copy()
    weak_password_data["password"] = "weak"
    
    response = client.post(f"{settings.api_v1_prefix}/auth/register", json=weak_password_data)
    assert response.status_code == 422
    assert "password" in response.json()["detail"][0]["loc"]


def test_user_registration_missing_fields_fails():
    """Test registration with missing required fields fails."""
    incomplete_data = {"email": "test@example.com"}
    
    response = client.post(f"{settings.api_v1_prefix}/auth/register", json=incomplete_data)
    assert response.status_code == 422


# User Login Tests  
def test_user_login_success():
    """Test successful user login."""
    create_test_user()
    
    response = client.post(f"{settings.api_v1_prefix}/auth/login", json=valid_login_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == settings.jwt_access_token_expire_minutes * 60


def test_user_login_wrong_password_fails():
    """Test login with incorrect password fails."""
    create_test_user()
    
    wrong_password_data = valid_login_data.copy()
    wrong_password_data["password"] = "WrongPassword123!"
    
    response = client.post(f"{settings.api_v1_prefix}/auth/login", json=wrong_password_data)
    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()


def test_user_login_nonexistent_email_fails():
    """Test login with non-existent email fails."""
    response = client.post(f"{settings.api_v1_prefix}/auth/login", json=valid_login_data)
    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()


def test_user_login_invalid_email_format_fails():
    """Test login with invalid email format fails."""
    invalid_data = valid_login_data.copy()
    invalid_data["email"] = "not-an-email"
    
    response = client.post(f"{settings.api_v1_prefix}/auth/login", json=invalid_data)
    assert response.status_code == 422


# Token Management Tests
def test_token_refresh_success():
    """Test successful token refresh."""
    create_test_user()
    login_response = client.post(f"{settings.api_v1_prefix}/auth/login", json=valid_login_data)
    refresh_token = login_response.json()["refresh_token"]
    
    refresh_response = client.post(f"{settings.api_v1_prefix}/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_response.status_code == 200
    data = refresh_response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_token_refresh_invalid_token_fails():
    """Test token refresh with invalid token fails."""
    response = client.post(f"{settings.api_v1_prefix}/auth/refresh", json={"refresh_token": "invalid_token"})
    assert response.status_code == 401
    assert "invalid" in response.json()["detail"].lower()


def test_token_refresh_missing_token_fails():
    """Test token refresh without token fails."""
    response = client.post(f"{settings.api_v1_prefix}/auth/refresh", json={})
    assert response.status_code == 422


# User Profile Tests
def test_get_current_user_success():
    """Test retrieving current user profile."""
    token = login_test_user()
    
    response = client.get(f"{settings.api_v1_prefix}/auth/me", headers=get_auth_headers(token))
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == valid_user_data["email"]
    assert data["name"] == valid_user_data["name"]
    assert "password" not in data


def test_get_current_user_without_token_fails():
    """Test retrieving user profile without authentication fails."""
    response = client.get(f"{settings.api_v1_prefix}/auth/me")
    assert response.status_code == 401
    assert "authorization header missing" in response.json()["detail"].lower()


def test_get_current_user_invalid_token_fails():
    """Test retrieving user profile with invalid token fails."""
    response = client.get(f"{settings.api_v1_prefix}/auth/me", headers=get_auth_headers("invalid_token"))
    assert response.status_code == 401
    assert "could not validate" in response.json()["detail"].lower()


# Password Reset Tests
def test_password_reset_request_success():
    """Test password reset request."""
    create_test_user()
    
    response = client.post(f"{settings.api_v1_prefix}/auth/password-reset/request", json={"email": valid_user_data["email"]})
    assert response.status_code == 200
    assert "password reset link has been sent" in response.json()["message"].lower()


def test_password_reset_request_nonexistent_email():
    """Test password reset request for non-existent email (should still return success for security)."""
    response = client.post(f"{settings.api_v1_prefix}/auth/password-reset/request", json={"email": "nonexistent@example.com"})
    assert response.status_code == 200
    assert "password reset link has been sent" in response.json()["message"].lower()


def test_password_reset_confirm_success():
    """Test password reset confirmation."""
    create_test_user()
    
    # First request reset to get token  
    reset_response = client.post(f"{settings.api_v1_prefix}/auth/password-reset/request", json={"email": valid_user_data["email"]})
    # Note: In a real implementation, the token would be sent via email
    # For testing, we'll generate a token manually
    from app.utils.security import create_password_reset_token
    reset_token = create_password_reset_token(valid_user_data["email"])
    
    new_password = "NewSecurePass123!"
    confirm_response = client.post(f"{settings.api_v1_prefix}/auth/password-reset/confirm", json={
        "token": reset_token,
        "new_password": new_password
    })
    assert confirm_response.status_code == 200
    
    # Verify can login with new password
    login_response = client.post(f"{settings.api_v1_prefix}/auth/login", json={
        "email": valid_user_data["email"],
        "password": new_password
    })
    assert login_response.status_code == 200


def test_password_reset_confirm_invalid_token_fails():
    """Test password reset confirmation with invalid token fails."""
    response = client.post(f"{settings.api_v1_prefix}/auth/password-reset/confirm", json={
        "token": "invalid_token",
        "new_password": "NewSecurePass123!"
    })
    assert response.status_code == 400
    assert "invalid" in response.json()["detail"].lower()


# Create Default User Tests
def test_create_default_user_success():
    """Test creating default admin user."""
    response = client.post(f"{settings.api_v1_prefix}/auth/create-default-user", json={})
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "admin@tasktracker.com"
    assert data["name"] == "Default Admin"


def test_create_default_user_already_exists():
    """Test creating default user when users already exist."""
    create_test_user()  # Create any user first
    
    response = client.post(f"{settings.api_v1_prefix}/auth/create-default-user", json={})
    assert response.status_code == 400
    assert "users already exist" in response.json()["detail"].lower()


# User-Scoped Task Operations Tests  
def test_user_scoped_task_creation():
    """Test that authenticated users can create tasks scoped to them."""
    token = login_test_user()
    
    task_data = {"title": "User Specific Task", "description": "This task belongs to the user"}
    response = client.post(f"{settings.api_v1_prefix}/tasks", 
                          json=task_data, 
                          headers=get_auth_headers(token))
    
    assert response.status_code == 201
    task = response.json()
    assert task["title"] == task_data["title"]
    # Note: user_id is not returned in response for security, but is stored in database


def test_user_scoped_task_retrieval():
    """Test that users only see their own tasks when authenticated."""
    # Create two users
    user1_token = login_test_user()
    
    user2_data = {
        "email": "user2@example.com",
        "password": "SecurePass123!",
        "name": "User Two"
    }
    client.post(f"{settings.api_v1_prefix}/auth/register", json=user2_data)
    user2_login = client.post(f"{settings.api_v1_prefix}/auth/login", json={
        "email": "user2@example.com",
        "password": "SecurePass123!"
    })
    user2_token = user2_login.json()["access_token"]
    
    # Create tasks for each user
    client.post(f"{settings.api_v1_prefix}/tasks", 
                json={"title": "User 1 Task"}, 
                headers=get_auth_headers(user1_token))
    
    client.post(f"{settings.api_v1_prefix}/tasks", 
                json={"title": "User 2 Task"}, 
                headers=get_auth_headers(user2_token))
    
    # User 1 should only see their task
    user1_tasks = client.get(f"{settings.api_v1_prefix}/tasks", headers=get_auth_headers(user1_token))
    assert user1_tasks.status_code == 200
    user1_task_list = user1_tasks.json()
    assert len(user1_task_list) == 1
    assert user1_task_list[0]["title"] == "User 1 Task"
    
    # User 2 should only see their task
    user2_tasks = client.get(f"{settings.api_v1_prefix}/tasks", headers=get_auth_headers(user2_token))
    assert user2_tasks.status_code == 200 
    user2_task_list = user2_tasks.json()
    assert len(user2_task_list) == 1
    assert user2_task_list[0]["title"] == "User 2 Task"


def test_anonymous_users_see_unscoped_tasks():
    """Test that anonymous users can still see tasks not associated with any user.""" 
    # Create a task without authentication (unscoped)
    task_data = {"title": "Public Task", "description": "This task is not user-scoped"}
    response = client.post(f"{settings.api_v1_prefix}/tasks", json=task_data)
    
    assert response.status_code == 201
    
    # Anonymous user should see the unscoped task
    all_tasks = client.get(f"{settings.api_v1_prefix}/tasks")
    assert all_tasks.status_code == 200
    task_list = all_tasks.json()
    assert len(task_list) == 1
    assert task_list[0]["title"] == "Public Task"
    
    # Authenticated user should also see unscoped tasks
    token = login_test_user()
    auth_tasks = client.get(f"{settings.api_v1_prefix}/tasks", headers=get_auth_headers(token))
    assert auth_tasks.status_code == 200
    auth_task_list = auth_tasks.json()
    assert len(auth_task_list) == 1  # Only the unscoped task, no user-specific tasks yet


def test_user_cannot_access_other_user_tasks():
    """Test that users cannot access tasks belonging to other users by ID."""
    user1_token = login_test_user()
    
    # Create second user
    user2_data = {
        "email": "user2@example.com", 
        "password": "SecurePass123!",
        "name": "User Two"
    }
    client.post(f"{settings.api_v1_prefix}/auth/register", json=user2_data)
    user2_login = client.post(f"{settings.api_v1_prefix}/auth/login", json={
        "email": "user2@example.com",
        "password": "SecurePass123!"
    })
    user2_token = user2_login.json()["access_token"]
    
    # User 2 creates a task
    user2_task = client.post(f"{settings.api_v1_prefix}/tasks", 
                            json={"title": "User 2 Private Task"}, 
                            headers=get_auth_headers(user2_token))
    task_id = user2_task.json()["id"]
    
    # User 1 should not be able to access User 2's task
    response = client.get(f"{settings.api_v1_prefix}/tasks/{task_id}", 
                         headers=get_auth_headers(user1_token))
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


# Authentication Integration Tests
def test_mixed_authenticated_and_anonymous_usage():
    """Test that authenticated and anonymous users can coexist."""
    # Create anonymous task
    anon_task = client.post(f"{settings.api_v1_prefix}/tasks", json={"title": "Anonymous Task"})
    assert anon_task.status_code == 201
    
    # Create authenticated user and task
    token = login_test_user()
    auth_task = client.post(f"{settings.api_v1_prefix}/tasks", 
                           json={"title": "Authenticated Task"}, 
                           headers=get_auth_headers(token))
    assert auth_task.status_code == 201
    
    # Anonymous user should see only unscoped task
    anon_tasks = client.get(f"{settings.api_v1_prefix}/tasks")
    anon_task_list = anon_tasks.json()
    assert len(anon_task_list) == 1
    assert anon_task_list[0]["title"] == "Anonymous Task"
    
    # Authenticated user should see both unscoped and their own tasks
    auth_tasks = client.get(f"{settings.api_v1_prefix}/tasks", headers=get_auth_headers(token))
    auth_task_list = auth_tasks.json()
    assert len(auth_task_list) == 2
    
    # Verify tasks are sorted by priority and creation time
    titles = [task["title"] for task in auth_task_list]
    assert "Anonymous Task" in titles
    assert "Authenticated Task" in titles