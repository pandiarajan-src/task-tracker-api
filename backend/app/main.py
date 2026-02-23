"""
Task Tracker API - FastAPI application with logging and API versioning.
Uses clean architecture with separated concerns: routes -> services -> database.
"""

import logging
import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.config import settings
from app.database import create_tables, get_db
from app.middleware.validation import ValidationMiddleware
from app.schemas import TaskCreate, TaskResponse, TaskUpdate
from app.services import task_service

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Rate limiter setup
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager - startup and shutdown logic."""
    logger.info("Starting Task Tracker API...")
    create_tables()
    logger.info("Database tables created/verified")
    yield
    logger.info("Shutting down Task Tracker API...")


app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    lifespan=lifespan,
)

# Add rate limiting
if settings.rate_limit_enabled:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add validation middleware
app.add_middleware(ValidationMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)


# Logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests with timing."""
    start_time = time.time()
    logger.info(f"Request: {request.method} {request.url.path}")

    response = await call_next(request)

    process_time = time.time() - start_time
    logger.info(f"Response: {response.status_code} - Duration: {process_time:.3f}s")
    return response


@app.get("/")
def read_root():
    """Root endpoint with API information."""
    logger.debug("Root endpoint accessed")
    return {
        "message": settings.app_name,
        "version": settings.app_version,
        "api_prefix": settings.api_v1_prefix,
    }


@app.get(f"{settings.api_v1_prefix}/tasks", response_model=list[TaskResponse])
def get_tasks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all tasks with optional pagination."""
    logger.info(f"Fetching tasks - skip: {skip}, limit: {limit}")
    tasks = task_service.get_all_tasks(db, skip=skip, limit=limit)
    logger.info(f"Retrieved {len(tasks)} tasks")
    return tasks


@app.get(f"{settings.api_v1_prefix}/tasks/{{task_id}}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    """Get a specific task by ID."""
    logger.info(f"Fetching task with id: {task_id}")
    task = task_service.get_task_by_id(db, task_id)
    if task is None:
        logger.warning(f"Task with id {task_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Task with id {task_id} not found"
        )
    logger.info(f"Task {task_id} retrieved successfully")
    return task


@app.post(
    f"{settings.api_v1_prefix}/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    """Create a new task."""
    logger.info(f"Creating new task: {task.title}")
    db_task = task_service.create_new_task(db, task)
    logger.info(f"Task created successfully with id: {db_task.id}")
    return db_task


@app.put(f"{settings.api_v1_prefix}/tasks/{{task_id}}", response_model=TaskResponse)
def update_task(task_id: int, task_update: TaskUpdate, db: Session = Depends(get_db)):
    """Update an existing task."""
    logger.info(f"Updating task with id: {task_id}")
    task = task_service.get_task_by_id(db, task_id)
    if task is None:
        logger.warning(f"Task with id {task_id} not found for update")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Task with id {task_id} not found"
        )

    updated_task = task_service.update_existing_task(db, task, task_update)
    logger.info(f"Task {task_id} updated successfully")
    return updated_task


@app.delete(f"{settings.api_v1_prefix}/tasks/{{task_id}}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """Delete a task by ID."""
    logger.info(f"Deleting task with id: {task_id}")
    task = task_service.get_task_by_id(db, task_id)
    if task is None:
        logger.warning(f"Task with id {task_id} not found for deletion")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Task with id {task_id} not found"
        )

    task_service.delete_task_by_id(db, task)
    logger.info(f"Task {task_id} deleted successfully")
    return {"message": f"Task with id {task_id} successfully deleted"}
