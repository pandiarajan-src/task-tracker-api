"""
Security utilities for authentication.
Handles password hashing and JWT token operations.
"""

import bcrypt
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt

from app.config import settings


def hash_password(password: str) -> str:
    """Hash a password with bcrypt."""
    # Convert password to bytes
    password_bytes = password.encode('utf-8')
    # Generate salt and hash
    salt = bcrypt.gensalt(rounds=settings.bcrypt_rounds)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    
    to_encode.update({"exp": expire, "type": "access"})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    
    return encoded_jwt


def create_refresh_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(days=settings.jwt_refresh_token_expire_days)
    
    to_encode.update({"exp": expire, "type": "refresh"})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> dict[str, Any] | None:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        
        # Check token type
        if payload.get("type") != token_type:
            return None
        
        # Check expiration
        exp = payload.get("exp")
        if exp is None:
            return None
        
        if datetime.fromtimestamp(exp, tz=UTC) < datetime.now(UTC):
            return None
        
        return payload
    
    except JWTError:
        return None


def create_password_reset_token(email: str) -> str:
    """Create a password reset token."""
    data = {"email": email, "type": "password_reset"}
    expires_delta = timedelta(hours=1)  # Password reset tokens expire in 1 hour
    expire = datetime.now(UTC) + expires_delta
    
    data.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        data,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    
    return encoded_jwt


def verify_password_reset_token(token: str) -> str | None:
    """Verify a password reset token and return the email."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        
        # Check token type
        if payload.get("type") != "password_reset":
            return None
        
        # Check expiration
        exp = payload.get("exp")
        if exp is None:
            return None
        
        if datetime.fromtimestamp(exp, tz=UTC) < datetime.now(UTC):
            return None
        
        return payload.get("email")
    
    except JWTError:
        return None