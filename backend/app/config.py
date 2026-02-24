"""
Configuration management for Task Tracker API.
Loads settings from environment variables with sensible defaults.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Allow unrelated env vars (e.g., CI tokens)
    )

    # App Info
    app_name: str = "Task Tracker API"
    app_version: str = "1.0.0"
    app_description: str = "A simple task tracker API built with FastAPI"

    # API Configuration
    api_v1_prefix: str = "/api/v1"

    # Database Configuration
    database_url: str = "sqlite:///./data/tasks.db"
    database_echo: bool = False

    # SQLAlchemy Pool Settings
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_pre_ping: bool = True

    # Logging
    log_level: str = "INFO"

    # CORS Settings
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    cors_allow_headers: list[str] = ["Authorization", "Content-Type", "Accept"]

    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_times: int = 100  # requests
    rate_limit_seconds: int = 60  # per 60 seconds
    
    # Enhanced Rate Limiting by Operation Type
    rate_limit_read_requests: int = 200  # GET operations
    rate_limit_write_requests: int = 50  # POST/PUT/DELETE operations
    rate_limit_auth_requests: int = 10   # Auth operations (login, register)
    rate_limit_period: str = "minute"    # Rate limit time window

    # Validation Settings
    max_request_size: int = 1048576  # 1MB in bytes
    enable_html_sanitization: bool = True
    enable_sql_sanitization: bool = True
    forbidden_words: list[str] = []
    validation_log_enabled: bool = True

    # Authentication Settings
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    
    # Password Settings
    password_min_length: int = 8
    bcrypt_rounds: int = 12
    
    # Feature Flags
    auth_required: bool = True  # Secure-by-default; override via env for local dev/tests

    # Transport Security
    enforce_https: bool = True
    
    # Email Settings (for password reset)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    from_email: str = "noreply@tasktracker.com"


# Global settings instance
settings = Settings()
