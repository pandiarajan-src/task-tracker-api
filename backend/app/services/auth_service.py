"""
Authentication service layer.
Handles user registration, login, and token operations.
"""

from datetime import UTC, datetime, timedelta
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.config import settings
from app.database import User
from app.schemas import Token, UserCreate, UserLogin, UserResponse
from app.utils.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
    verify_token,
)


class AuthService:
    """Service for authentication operations."""

    @staticmethod
    def create_user(db: Session, user_create: UserCreate) -> User:
        """Create a new user account."""
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user_create.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email address is already registered"
            )
        
        # Hash the password
        hashed_password = hash_password(user_create.password)
        
        # Create new user
        db_user = User(
            email=user_create.email,
            name=user_create.name,
            hashed_password=hashed_password,
            is_active=True
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        return db_user

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> User | None:
        """Authenticate a user with email and password."""
        user = db.query(User).filter(
            and_(User.email == email, User.is_active == True)
        ).first()
        
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        return user

    @staticmethod
    def login_user(db: Session, user_login: UserLogin) -> Token:
        """Login user and return JWT tokens."""
        user = AuthService.authenticate_user(
            db, user_login.email, user_login.password
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create tokens
        access_token_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
        refresh_token_expires = timedelta(days=settings.jwt_refresh_token_expire_days)
        
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email},
            expires_delta=access_token_expires
        )
        
        refresh_token = create_refresh_token(
            data={"sub": str(user.id), "email": user.email},
            expires_delta=refresh_token_expires
        )
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=int(access_token_expires.total_seconds())
        )

    @staticmethod
    def refresh_access_token(db: Session, refresh_token: str) -> Token:
        """Refresh access token using refresh token."""
        # Verify refresh token
        payload = verify_token(refresh_token, token_type="refresh")
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = db.query(User).filter(
            and_(User.id == int(user_id), User.is_active == True)
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create new tokens
        access_token_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
        refresh_token_expires = timedelta(days=settings.jwt_refresh_token_expire_days)
        
        new_access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email},
            expires_delta=access_token_expires
        )
        
        new_refresh_token = create_refresh_token(
            data={"sub": str(user.id), "email": user.email},
            expires_delta=refresh_token_expires
        )
        
        return Token(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=int(access_token_expires.total_seconds())
        )

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> User | None:
        """Get user by ID."""
        return db.query(User).filter(
            and_(User.id == user_id, User.is_active == True)
        ).first()

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> User | None:
        """Get user by email."""
        return db.query(User).filter(
            and_(User.email == email, User.is_active == True)
        ).first()

    @staticmethod
    def get_current_user_from_token(db: Session, token: str) -> User:
        """Get current user from JWT token."""
        # Verify access token
        payload = verify_token(token, token_type="access")
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user ID from token
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user from database
        user = AuthService.get_user_by_id(db, int(user_id))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user

    @staticmethod
    def reset_password(db: Session, email: str, new_password: str) -> bool:
        """Reset user password."""
        user = AuthService.get_user_by_email(db, email)
        if not user:
            return False
        
        # Hash new password
        hashed_password = hash_password(new_password)
        
        # Update password
        user.hashed_password = hashed_password
        user.updated_at = datetime.now(UTC)
        
        db.commit()
        return True

    @staticmethod
    def create_default_user(db: Session) -> User:
        """Create a default user for development/migration purposes."""
        default_email = "admin@tasktracker.com"
        existing_user = db.query(User).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Users already exist",
            )
        
        # Create default user
        user_create = UserCreate(
            email=default_email,
            name="Default Admin",
            password="AdminPass123!"
        )
        
        return AuthService.create_user(db, user_create)