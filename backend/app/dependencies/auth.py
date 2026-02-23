"""
Authentication middleware and dependencies.
Handles JWT token validation and user authentication.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import User, get_db
from app.services.auth_service import AuthService
from app.config import settings

# HTTP Bearer token scheme
security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user.
    Raises HTTPException if authentication fails.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    return AuthService.get_current_user_from_token(db, token)


def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db)
) -> User | None:
    """
    Optional dependency to get the current authenticated user.
    Returns None if authentication fails instead of raising an exception.
    Used for gradual migration where auth is optional.
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        return AuthService.get_current_user_from_token(db, token)
    except HTTPException:
        return None


def require_auth() -> User:
    """
    Dependency that always requires authentication.
    Used when auth_required flag is True.
    """
    return Depends(get_current_user)


def optional_auth() -> User | None:
    """
    Dependency that optionally allows authentication.
    Used during gradual migration when auth_required flag is False.
    """
    return Depends(get_current_user_optional)


def get_auth_dependency():
    """
    Dynamic dependency that returns the appropriate dependency function based on config.
    Returns the actual dependency function, not a Depends wrapper.
    """
    if settings.auth_required:
        return get_current_user
    else:
        return get_current_user_optional