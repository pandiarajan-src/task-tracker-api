"""
Task service layer - business logic for task operations.
Separates database operations from API routes.
"""

from datetime import UTC, datetime

from sqlalchemy import case, desc, or_
from sqlalchemy.orm import Session

from app.database import Task, TaskPriority
from app.schemas import Priority, TaskCreate, TaskUpdate


def get_all_tasks(
    db: Session, 
    skip: int = 0, 
    limit: int = 100, 
    priority_filter: Priority | None = None,
    user_id: int | None = None
) -> list[Task]:
    """Retrieve all tasks with pagination, filtering, and priority sorting."""
    query = db.query(Task)
    
    # Apply user filter if specified (for user scoping)
    if user_id is not None:
        query = query.filter(or_(Task.user_id == user_id, Task.user_id.is_(None)))
    else:
        query = query.filter(Task.user_id.is_(None))
    
    # Apply priority filter if specified
    if priority_filter:
        query = query.filter(Task.priority == TaskPriority(priority_filter.value))
    
    # Sort by priority (high -> medium -> low), then by created_at desc
    priority_case = case(
        (Task.priority == TaskPriority.HIGH, 1),
        (Task.priority == TaskPriority.MEDIUM, 2),
        (Task.priority == TaskPriority.LOW, 3)
    )
    
    return query.order_by(priority_case, desc(Task.created_at)).offset(skip).limit(limit).all()


def get_task_by_id(db: Session, task_id: int, user_id: int | None = None) -> Task | None:
    """Retrieve a specific task by ID with optional user scoping."""
    query = db.query(Task).filter(Task.id == task_id)
    
    # Apply user filter if specified (for user scoping)
    if user_id is not None:
        query = query.filter(or_(Task.user_id == user_id, Task.user_id.is_(None)))
    else:
        query = query.filter(Task.user_id.is_(None))
    
    return query.first()


def create_new_task(db: Session, task_data: TaskCreate, user_id: int | None = None) -> Task:
    """Create a new task in the database with optional user association."""
    # Convert Priority enum to TaskPriority enum
    priority_value = TaskPriority(task_data.priority.value)
    
    db_task = Task(
        title=task_data.title, 
        description=task_data.description, 
        completed=task_data.completed,
        priority=priority_value,
        user_id=user_id  # Associate with user if provided
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
            if key == "priority" and value is not None:
                # Convert Priority enum to TaskPriority enum
                setattr(task, key, TaskPriority(value.value))
            else:
                setattr(task, key, value)
        task.updated_at = datetime.now(UTC)
        db.commit()
        db.refresh(task)
    return task


def delete_task_by_id(db: Session, task: Task) -> None:
    """Delete a task from the database."""
    db.delete(task)
    db.commit()
