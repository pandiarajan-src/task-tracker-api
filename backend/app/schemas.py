from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.config import settings
from app.utils.sanitizer import check_forbidden_words, check_sql_injection, sanitize_string


class Priority(str, Enum):
    """Task priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    completed: bool = False
    priority: Priority = Priority.MEDIUM


class TaskCreate(TaskBase):
    """Schema for creating a new task with enhanced validation."""

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Validate and sanitize task title."""
        # Store original for comparison
        original = v
        
        # Sanitize the title
        sanitized = sanitize_string(v)
        if not sanitized:
            raise ValueError("Title cannot be empty after sanitization")
        
        # Reject if HTML was stripped (indicates HTML was present)
        if original != sanitized and settings.enable_html_sanitization:
            raise ValueError("Title contains forbidden HTML tags or special characters")
        
        # Check for SQL injection
        if check_sql_injection(sanitized):
            raise ValueError("Title contains invalid characters or patterns")
        
        # Check for forbidden words
        forbidden = check_forbidden_words(sanitized)
        if forbidden:
            raise ValueError(f"Title contains forbidden words: {', '.join(forbidden)}")
        
        # Check for dangerous characters
        dangerous_chars = ["<", ">", "{", "}", "[", "]"]
        if any(char in sanitized for char in dangerous_chars):
            raise ValueError("Title contains forbidden special characters")
        
        return sanitized

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str | None) -> str | None:
        """Validate and sanitize task description."""
        if v is None:
            return v
        
        # Sanitize the description
        sanitized = sanitize_string(v)
        
        # Check for SQL injection
        if check_sql_injection(sanitized):
            raise ValueError("Description contains invalid characters or patterns")
        
        # Check for forbidden words
        forbidden = check_forbidden_words(sanitized)
        if forbidden:
            raise ValueError(
                f"Description contains forbidden words: {', '.join(forbidden)}"
            )
        
        return sanitized


class TaskUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    completed: bool | None = None
    priority: Priority | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str | None) -> str | None:
        """Validate and sanitize task title."""
        if v is None:
            return v
        
        # Store original for comparison
        original = v
        
        # Sanitize the title
        sanitized = sanitize_string(v)
        if not sanitized:
            raise ValueError("Title cannot be empty after sanitization")
        
        # Reject if HTML was stripped (indicates HTML was present)
        if original != sanitized and settings.enable_html_sanitization:
            raise ValueError("Title contains forbidden HTML tags or special characters")
        
        # Check for SQL injection
        if check_sql_injection(sanitized):
            raise ValueError("Title contains invalid characters or patterns")
        
        # Check for forbidden words
        forbidden = check_forbidden_words(sanitized)
        if forbidden:
            raise ValueError(f"Title contains forbidden words: {', '.join(forbidden)}")
        
        # Check for dangerous characters
        dangerous_chars = ["<", ">", "{", "}", "[", "]"]
        if any(char in sanitized for char in dangerous_chars):
            raise ValueError("Title contains forbidden special characters")
        
        return sanitized

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str | None) -> str | None:
        """Validate and sanitize task description."""
        if v is None:
            return v
        
        # Sanitize the description
        sanitized = sanitize_string(v)
        
        # Check for SQL injection
        if check_sql_injection(sanitized):
            raise ValueError("Description contains invalid characters or patterns")
        
        # Check for forbidden words
        forbidden = check_forbidden_words(sanitized)
        if forbidden:
            raise ValueError(
                f"Description contains forbidden words: {', '.join(forbidden)}"
            )
        
        return sanitized


class TaskResponse(TaskBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# User Authentication Schemas
class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=100)


class UserCreate(UserBase):
    """Schema for user registration with enhanced validation."""
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate and sanitize user name."""
        # Store original for comparison
        original = v
        
        # Sanitize the name
        sanitized = sanitize_string(v)
        if not sanitized:
            raise ValueError("Name cannot be empty after sanitization")
        
        # Reject if HTML was stripped (indicates HTML was present)
        if original != sanitized and settings.enable_html_sanitization:
            raise ValueError("Name contains forbidden HTML tags or special characters")
        
        # Check for SQL injection
        if check_sql_injection(sanitized):
            raise ValueError("Name contains invalid characters or patterns")
        
        # Check for forbidden words
        forbidden = check_forbidden_words(sanitized)
        if forbidden:
            raise ValueError(f"Name contains forbidden words: {', '.join(forbidden)}")
        
        # Check for dangerous characters
        dangerous_chars = ["<", ">", "{", "}", "[", "]"]
        if any(char in sanitized for char in dangerous_chars):
            raise ValueError("Name contains forbidden special characters")
        
        return sanitized

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < settings.password_min_length:
            raise ValueError(f"Password must be at least {settings.password_min_length} characters long")
        
        # Basic password strength requirements
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        
        if not (has_upper and has_lower and has_digit):
            raise ValueError("Password must contain at least one uppercase letter, one lowercase letter, and one digit")
        
        return v


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class UserResponse(UserBase):
    """Schema for user response (excludes sensitive data)."""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    """Schema for updating user information."""
    name: str | None = Field(None, min_length=1, max_length=100)
    email: EmailStr | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        """Validate and sanitize user name."""
        if v is None:
            return v
            
        # Store original for comparison
        original = v
        
        # Sanitize the name
        sanitized = sanitize_string(v)
        if not sanitized:
            raise ValueError("Name cannot be empty after sanitization")
        
        # Reject if HTML was stripped (indicates HTML was present)
        if original != sanitized and settings.enable_html_sanitization:
            raise ValueError("Name contains forbidden HTML tags or special characters")
        
        # Check for SQL injection
        if check_sql_injection(sanitized):
            raise ValueError("Name contains invalid characters or patterns")
        
        # Check for forbidden words
        forbidden = check_forbidden_words(sanitized)
        if forbidden:
            raise ValueError(f"Name contains forbidden words: {', '.join(forbidden)}")
        
        # Check for dangerous characters
        dangerous_chars = ["<", ">", "{", "}", "[", "]"]
        if any(char in sanitized for char in dangerous_chars):
            raise ValueError("Name contains forbidden special characters")
        
        return sanitized


# Authentication Token Schemas
class Token(BaseModel):
    """JWT token response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenRefresh(BaseModel):
    """Schema for token refresh request."""
    refresh_token: str


class PasswordResetRequest(BaseModel):
    """Schema for password reset request."""
    email: EmailStr


class PasswordReset(BaseModel):
    """Schema for password reset with token."""
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < settings.password_min_length:
            raise ValueError(f"Password must be at least {settings.password_min_length} characters long")
        
        # Basic password strength requirements
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        
        if not (has_upper and has_lower and has_digit):
            raise ValueError("Password must contain at least one uppercase letter, one lowercase letter, and one digit")
        
        return v

