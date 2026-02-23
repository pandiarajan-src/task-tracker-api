from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.config import settings
from app.utils.sanitizer import check_forbidden_words, check_sql_injection, sanitize_string


class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    completed: bool = False


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

