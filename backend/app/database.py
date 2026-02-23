"""
Database models and session management.
Uses SQLAlchemy with connection pooling and timezone-aware timestamps.
"""

import enum
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

from app.config import settings


class TaskPriority(enum.Enum):
    """Task priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

# Ensure data directory exists
data_dir = Path("data")
data_dir.mkdir(exist_ok=True)

# Create engine with connection pooling
engine = create_engine(
    settings.database_url,
    echo=settings.database_echo,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    pool_size=settings.pool_size,
    max_overflow=settings.max_overflow,
    pool_timeout=settings.pool_timeout,
    pool_pre_ping=settings.pool_pre_ping,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class User(Base):
    """User model with authentication and profile information."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationship - commented out for now to avoid SQLite FK issues
    # tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")


class Task(Base):
    """Task model with auto-managed timestamps and priority."""

    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    completed = Column(Boolean, default=False, nullable=False)
    priority = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # Nullable for gradual migration
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationship - commented out for now to avoid SQLite FK issues
    # user = relationship("User", back_populates="tasks")


def create_tables():
    """Create all tables in the database."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Database session dependency for FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
