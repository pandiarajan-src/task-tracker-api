"""
Task service layer - business logic for task operations.
Separates database operations from API routes.
"""

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.database import Task
from app.schemas import TaskCreate, TaskUpdate


def get_all_tasks(db: Session, skip: int = 0, limit: int = 100) -> list[Task]:
    """Retrieve all tasks with pagination."""
    return db.query(Task).offset(skip).limit(limit).all()


def get_task_by_id(db: Session, task_id: int) -> Task | None:
    """Retrieve a specific task by ID."""
    return db.query(Task).filter(Task.id == task_id).first()


def create_new_task(db: Session, task_data: TaskCreate) -> Task:
    """Create a new task in the database."""
    db_task = Task(
        title=task_data.title, description=task_data.description, completed=task_data.completed
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def update_existing_task(db: Session, task: Task, task_update: TaskUpdate) -> Task:
    """Update an existing task with partial data."""
    update_data = task_update.model_dump(exclude_unset=True)
    if update_data:
        for key, value in update_data.items():
            setattr(task, key, value)
        task.updated_at = datetime.now(UTC)
        db.commit()
        db.refresh(task)
    return task


def delete_task_by_id(db: Session, task: Task) -> None:
    """Delete a task from the database."""
    db.delete(task)
    db.commit()
