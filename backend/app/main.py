"""
Task Tracker API - FastAPI application with logging and API versioning.
Uses clean architecture with separated concerns: routes -> services -> database.
"""

import logging
import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy.orm import Session

from app.config import settings
from app.database import User, create_tables, get_db
from app.dependencies.auth import get_auth_dependency
from app.middleware.validation import ValidationMiddleware
from app.rate_limiter import limiter
from app.routes import auth_router
from app.schemas import Priority, TaskCreate, TaskResponse, TaskUpdate
from app.services import task_service

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


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


# Include routers
app.include_router(auth_router, prefix=settings.api_v1_prefix)


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
@limiter.limit(f"{settings.rate_limit_read_requests}/{settings.rate_limit_period}")
def get_tasks(
    request: Request,
    skip: int = 0, 
    limit: int = 100, 
    priority: Priority | None = None,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_auth_dependency())
):
    """Get all tasks with optional pagination and priority filtering."""
    user_id = current_user.id if current_user else None
    
    if priority:
        logger.info(f"Fetching tasks - skip: {skip}, limit: {limit}, priority: {priority.value}, user_id: {user_id}")
    else:
        logger.info(f"Fetching tasks - skip: {skip}, limit: {limit}, user_id: {user_id}")
    
    tasks = task_service.get_all_tasks(db, skip=skip, limit=limit, priority_filter=priority, user_id=user_id)
    logger.info(f"Retrieved {len(tasks)} tasks")
    return tasks


@app.get(f"{settings.api_v1_prefix}/tasks/{{task_id}}", response_model=TaskResponse)
@limiter.limit(f"{settings.rate_limit_read_requests}/{settings.rate_limit_period}")
def get_task(
    request: Request,
    task_id: int, 
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_auth_dependency())
):
    """Get a specific task by ID."""
    user_id = current_user.id if current_user else None
    logger.info(f"Fetching task with id: {task_id}, user_id: {user_id}")
    
    task = task_service.get_task_by_id(db, task_id, user_id=user_id)
    if task is None:
        logger.warning(f"Task with id {task_id} not found for user {user_id}")
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
@limiter.limit(f"{settings.rate_limit_write_requests}/{settings.rate_limit_period}")
def create_task(
    request: Request,
    task: TaskCreate, 
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_auth_dependency())
):
    """Create a new task."""
    user_id = current_user.id if current_user else None
    logger.info(f"Creating new task: {task.title}, user_id: {user_id}")
    
    db_task = task_service.create_new_task(db, task, user_id=user_id)
    logger.info(f"Task created successfully with id: {db_task.id}")
    return db_task


@app.put(f"{settings.api_v1_prefix}/tasks/{{task_id}}", response_model=TaskResponse)
@limiter.limit(f"{settings.rate_limit_write_requests}/{settings.rate_limit_period}")
def update_task(
    request: Request,
    task_id: int, 
    task_update: TaskUpdate, 
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_auth_dependency())
):
    """Update an existing task."""
    user_id = current_user.id if current_user else None
    logger.info(f"Updating task with id: {task_id}, user_id: {user_id}")
    
    task = task_service.get_task_by_id(db, task_id, user_id=user_id)
    if task is None:
        logger.warning(f"Task with id {task_id} not found for update by user {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Task with id {task_id} not found"
        )

    updated_task = task_service.update_existing_task(db, task, task_update)
    logger.info(f"Task {task_id} updated successfully")
    return updated_task


@app.delete(f"{settings.api_v1_prefix}/tasks/{{task_id}}")
@limiter.limit(f"{settings.rate_limit_write_requests}/{settings.rate_limit_period}")
def delete_task(
    request: Request,
    task_id: int, 
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_auth_dependency())
):
    """Delete a task by ID."""
    user_id = current_user.id if current_user else None
    logger.info(f"Deleting task with id: {task_id}, user_id: {user_id}")
    
    task = task_service.get_task_by_id(db, task_id, user_id=user_id)
    if task is None:
        logger.warning(f"Task with id {task_id} not found for deletion by user {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Task with id {task_id} not found"
        )

    task_service.delete_task_by_id(db, task)
    logger.info(f"Task {task_id} deleted successfully")
    return {"message": f"Task with id {task_id} successfully deleted"}
