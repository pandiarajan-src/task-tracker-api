"""
Tests for rate limiting functionality.
Verifies that rate limiting is applied to all API endpoints and returns 429 when exceeded.
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
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_rate_limit.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


client = TestClient(app)


@pytest.fixture(scope="function", autouse=True)
def setup_rate_limit_tests():
    """Set up and tear down for rate limiting tests."""
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    limiter.reset()
    limiter.enabled = True
    yield
    limiter.reset()
    limiter.enabled = True
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.pop(get_db, None)


# Rate limit configuration tests
def test_all_task_endpoints_have_rate_limiting_configured():
    """Test that all task API endpoints have rate limiting configured."""
    rate_limited_routes = set(limiter._route_limits.keys())
    expected_task_routes = {
        "app.main.read_root",
        "app.main.get_tasks",
        "app.main.get_task",
        "app.main.create_task",
        "app.main.update_task",
        "app.main.delete_task",
    }
    for route in expected_task_routes:
        assert route in rate_limited_routes, f"Rate limiting not configured for {route}"


def test_all_auth_endpoints_have_rate_limiting_configured():
    """Test that all auth API endpoints have rate limiting configured."""
    rate_limited_routes = set(limiter._route_limits.keys())
    expected_auth_routes = {
        "app.routes.auth.register_user",
        "app.routes.auth.login_user",
        "app.routes.auth.refresh_token",
        "app.routes.auth.get_current_user_info",
        "app.routes.auth.request_password_reset",
        "app.routes.auth.confirm_password_reset",
        "app.routes.auth.create_default_user",
    }
    for route in expected_auth_routes:
        assert route in rate_limited_routes, f"Rate limiting not configured for {route}"


def test_read_endpoints_use_read_limit():
    """Test that read endpoints are configured with the read request limit."""
    read_limit_str = f"{settings.rate_limit_read_requests} per 1 {settings.rate_limit_period}"
    read_routes = ["app.main.read_root", "app.main.get_tasks", "app.main.get_task"]
    for route in read_routes:
        limit = limiter._route_limits[route][0].limit
        assert str(limit) == read_limit_str, f"{route} has unexpected limit: {limit}"


def test_write_endpoints_use_write_limit():
    """Test that write endpoints are configured with the write request limit."""
    write_limit_str = f"{settings.rate_limit_write_requests} per 1 {settings.rate_limit_period}"
    write_routes = ["app.main.create_task", "app.main.update_task", "app.main.delete_task"]
    for route in write_routes:
        limit = limiter._route_limits[route][0].limit
        assert str(limit) == write_limit_str, f"{route} has unexpected limit: {limit}"


def test_auth_endpoints_use_auth_limit():
    """Test that auth endpoints are configured with the auth request limit."""
    auth_limit_str = f"{settings.rate_limit_auth_requests} per 1 {settings.rate_limit_period}"
    auth_routes = [
        "app.routes.auth.register_user",
        "app.routes.auth.login_user",
        "app.routes.auth.refresh_token",
        "app.routes.auth.request_password_reset",
        "app.routes.auth.confirm_password_reset",
        "app.routes.auth.create_default_user",
    ]
    for route in auth_routes:
        limit = limiter._route_limits[route][0].limit
        assert str(limit) == auth_limit_str, f"{route} has unexpected limit: {limit}"


# Rate limiting enforcement tests
def test_rate_limiting_returns_429_when_auth_limit_exceeded():
    """Test that rate limiting returns 429 when the auth endpoint limit is exceeded."""
    auth_limit = settings.rate_limit_auth_requests

    # Make requests up to the limit (with invalid credentials to avoid side effects)
    for i in range(auth_limit):
        client.post(
            f"{settings.api_v1_prefix}/auth/login",
            json={"email": f"user{i}@example.com", "password": "wrongpassword"},
        )

    # The next request should be rate limited
    response = client.post(
        f"{settings.api_v1_prefix}/auth/login",
        json={"email": "test@example.com", "password": "testpassword"},
    )
    assert response.status_code == 429


def test_rate_limiting_returns_429_when_write_limit_exceeded():
    """Test that rate limiting returns 429 when the write endpoint limit is exceeded."""
    write_limit = settings.rate_limit_write_requests

    # Make requests up to the write limit (with invalid data to keep responses fast)
    for i in range(write_limit):
        client.post(
            f"{settings.api_v1_prefix}/tasks",
            json={"title": f"Task {i}"},
        )

    # The next request should be rate limited
    response = client.post(
        f"{settings.api_v1_prefix}/tasks",
        json={"title": "Should be rate limited"},
    )
    assert response.status_code == 429


def test_rate_limit_not_exceeded_within_limits_returns_200():
    """Test that requests within the rate limit are allowed (happy path).

    Uses unauthenticated requests since auth_required is False by default,
    allowing anonymous access to these endpoints.
    """
    response = client.get("/")
    assert response.status_code == 200

    # Unauthenticated requests are allowed (auth_required=False in settings)
    response = client.get(f"{settings.api_v1_prefix}/tasks")
    assert response.status_code == 200
