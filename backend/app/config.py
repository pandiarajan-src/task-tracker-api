"""
Configuration management for Task Tracker API.
Loads settings from environment variables with sensible defaults.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

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
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]

    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_times: int = 100  # requests
    rate_limit_seconds: int = 60  # per 60 seconds

    # Validation Settings
    max_request_size: int = 1048576  # 1MB in bytes
    enable_html_sanitization: bool = True
    enable_sql_sanitization: bool = True
    forbidden_words: list[str] = []
    validation_log_enabled: bool = True


# Global settings instance
settings = Settings()
