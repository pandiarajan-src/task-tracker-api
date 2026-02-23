"""
Input sanitization utilities for cleaning and validating user input.
Heuristic checks flag suspicious patterns but are not a security boundary.
"""

import logging
import re

import bleach

from app.config import settings

logger = logging.getLogger(__name__)

# Allowed HTML tags (empty list = strip all HTML)
ALLOWED_TAGS = []
ALLOWED_ATTRIBUTES = {}

# SQL injection patterns to detect (must be standalone keywords)
SQL_PATTERNS = [
    r"\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b.*\b(FROM|INTO|WHERE|TABLE)\b",
    r"(--|;)\s*(SELECT|INSERT|UPDATE|DELETE|DROP)",
    r"\bOR\b\s+\d+\s*=\s*\d+",
    r"\bAND\b\s+\d+\s*=\s*\d+",
    r"'\s*(OR|AND)\s+'",
]


def sanitize_html(text: str | None) -> str | None:
    """
    Remove dangerous HTML tags and attributes from text.
    
    Args:
        text: Input string that may contain HTML
        
    Returns:
        Sanitized string with HTML stripped
    """
    if not text or not settings.enable_html_sanitization:
        return text
    
    # Use bleach to clean HTML
    cleaned = bleach.clean(
        text, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True
    )
    
    # Log if content was modified
    if cleaned != text:
        logger.warning(f"HTML content sanitized: '{text[:50]}...' -> '{cleaned[:50]}...'")
    
    return cleaned


def sanitize_string(text: str | None) -> str | None:
    """
    Clean and normalize string input.
    
    Args:
        text: Input string to clean
        
    Returns:
        Cleaned and normalized string
    """
    if not text:
        return text
    
    # Strip whitespace
    text = text.strip()
    
    # Normalize whitespace (replace multiple spaces with single space)
    text = re.sub(r"\s+", " ", text)
    
    # Sanitize HTML if enabled
    if settings.enable_html_sanitization:
        text = sanitize_html(text)
    
    return text


def check_sql_injection(text: str | None) -> bool:
    """
    Check if text contains potential SQL injection patterns.
    This is a best-effort heuristic and does not replace parameterized queries.
    
    Args:
        text: Input string to check
        
    Returns:
        True if suspicious SQL patterns detected, False otherwise
    """
    if not text or not settings.enable_sql_sanitization:
        return False
    
    text_upper = text.upper()
    
    for pattern in SQL_PATTERNS:
        if re.search(pattern, text_upper, re.IGNORECASE):
            logger.warning(f"Potential SQL injection detected: {text[:100]}")
            return True
    
    return False


def check_forbidden_words(text: str | None) -> list[str]:
    """
    Check if text contains forbidden words.
    
    Args:
        text: Input string to check
        
    Returns:
        List of forbidden words found (empty if none)
    """
    if not text or not settings.forbidden_words:
        return []
    
    text_lower = text.lower()
    found_words = []
    
    for word in settings.forbidden_words:
        if word.lower() in text_lower:
            found_words.append(word)
    
    if found_words:
        logger.warning(f"Forbidden words found: {found_words}")
    
    return found_words


def sanitize_input(text: str | None, check_sql: bool = True) -> tuple[str | None, list[str]]:
    """
    Comprehensive input sanitization with validation.
    
    Args:
        text: Input string to sanitize
        check_sql: Whether to check for SQL injection patterns
        
    Returns:
        Tuple of (sanitized_text, list of validation errors)
    """
    if not text:
        return text, []
    
    errors = []
    
    # Check for SQL injection
    if check_sql and check_sql_injection(text):
        errors.append("Input contains suspicious SQL patterns")
    
    # Check for forbidden words
    forbidden = check_forbidden_words(text)
    if forbidden:
        errors.append(f"Input contains forbidden words: {', '.join(forbidden)}")
    
    # Sanitize the text
    sanitized = sanitize_string(text)
    
    return sanitized, errors
