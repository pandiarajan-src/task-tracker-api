"""
Authentication routes for user registration, login, and token management.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

# Import rate limiter from shared module
from app.rate_limiter import limiter
from app.config import settings
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.schemas import (
    PasswordReset,
    PasswordResetRequest,
    Token,
    TokenRefresh,
    UserCreate,
    UserLogin,
    UserResponse,
)
from app.services.auth_service import AuthService
from app.utils.security import create_password_reset_token, verify_password_reset_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(f"{settings.rate_limit_auth_requests}/{settings.rate_limit_period}")
def register_user(
    request: Request,
    user_create: UserCreate,
    db: Session = Depends(get_db)
) -> UserResponse:
    """Register a new user account."""
    logger.info(f"User registration attempt for email: {user_create.email}")
    # Allow HTTPExceptions from the service layer to surface for client feedback.
    
    try:
        user = AuthService.create_user(db, user_create)
        logger.info(f"User registered successfully: {user.email}")
        
        return UserResponse.model_validate(user)
    
    except HTTPException as e:
        logger.warning(f"Registration failed for {user_create.email}: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during registration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed due to internal error"
        )


@router.post("/login", response_model=Token)
@limiter.limit(f"{settings.rate_limit_auth_requests}/{settings.rate_limit_period}")
def login_user(
    request: Request,
    user_login: UserLogin,
    db: Session = Depends(get_db)
) -> Token:
    """Authenticate user and return JWT tokens."""
    logger.info(f"Login attempt for email: {user_login.email}")
    # Ensure token creation only happens after successful authentication.
    
    try:
        token = AuthService.login_user(db, user_login)
        logger.info(f"Login successful for: {user_login.email}")
        
        return token
    
    except HTTPException as e:
        logger.warning(f"Login failed for {user_login.email}: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed due to internal error"
        )


@router.post("/refresh", response_model=Token)
@limiter.limit(f"{settings.rate_limit_auth_requests}/{settings.rate_limit_period}")
def refresh_token(
    request: Request,
    token_refresh: TokenRefresh,
    db: Session = Depends(get_db)
) -> Token:
    """Refresh access token using refresh token."""
    logger.info("Token refresh attempt")
    # Verify the refresh token before issuing new credentials.
    
    try:
        new_token = AuthService.refresh_access_token(db, token_refresh.refresh_token)
        logger.info("Token refresh successful")
        
        return new_token
    
    except HTTPException as e:
        logger.warning(f"Token refresh failed: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during token refresh: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed due to internal error"
        )


@router.get("/me", response_model=UserResponse)
@limiter.limit(f"{settings.rate_limit_read_requests}/{settings.rate_limit_period}")
def get_current_user_info(
    request: Request,
    current_user = Depends(get_current_user)
) -> UserResponse:
    """Get current user information."""
    logger.info(f"User info request for: {current_user.email}")
    # Return the sanitized user data provided by the dependency.
    
    return UserResponse.model_validate(current_user)


@router.post("/password-reset/request")
@limiter.limit(f"{settings.rate_limit_auth_requests}/{settings.rate_limit_period}")
def request_password_reset(
    request: Request,
    password_reset_request: PasswordResetRequest,
    db: Session = Depends(get_db)
) -> dict[str, str]:
    """Request password reset token."""
    logger.info(f"Password reset request for: {password_reset_request.email}")
    
    # Check if user exists
    user = AuthService.get_user_by_email(db, password_reset_request.email)
    if not user:
        # Don't reveal if email exists or not for security
        logger.warning(f"Password reset requested for non-existent email: {password_reset_request.email}")
    else:
        # Generate reset token
        reset_token = create_password_reset_token(password_reset_request.email)
        logger.info(f"Password reset token generated for: {password_reset_request.email}")
        
        # TODO: Send email with reset token
        # For now, we'll log it (in production, send via email service)
        logger.info(f"Password reset token (TODO: send via email): {reset_token}")
    
    # Always return success to prevent email enumeration
    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/password-reset/confirm")
@limiter.limit(f"{settings.rate_limit_auth_requests}/{settings.rate_limit_period}")
def confirm_password_reset(
    request: Request,
    password_reset: PasswordReset,
    db: Session = Depends(get_db)
) -> dict[str, str]:
    """Reset password using reset token."""
    logger.info("Password reset confirmation attempt")
    
    # Verify reset token
    email = verify_password_reset_token(password_reset.token)
    if not email:
        logger.warning("Invalid or expired password reset token")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Reset password
    success = AuthService.reset_password(db, email, password_reset.new_password)
    if not success:
        logger.error(f"Password reset failed for email: {email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset failed"
        )
    
    logger.info(f"Password reset successful for: {email}")
    return {"message": "Password reset successful"}


@router.post("/create-default-user", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(f"{settings.rate_limit_auth_requests}/{settings.rate_limit_period}")
def create_default_user(
    request: Request,
    db: Session = Depends(get_db)
) -> UserResponse:
    """Create default user for development/migration purposes."""
    logger.info("Creating default user")
    # Guard creation so migrations only run when no users exist yet.
    
    try:
        user = AuthService.create_default_user(db)
        logger.info(f"Default user created/retrieved: {user.email}")
        
        return UserResponse.model_validate(user)

    except HTTPException as e:
        logger.warning(f"Default user creation failed: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"Error creating default user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create default user"
        )
