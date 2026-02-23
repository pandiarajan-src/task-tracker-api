# Backend - Task Tracker API

## New Project Structure

```
backend/
├── app/                        # Application package
│   ├── __init__.py
│   ├── config.py              # Configuration management
│   ├── database.py            # Database models and connection
│   ├── schemas.py             # Pydantic validation schemas
│   ├── main.py                # FastAPI application with routes
│   ├── test_main.py           # Test suite
│   └── services/              # Business logic layer
│       ├── __init__.py
│       └── task_service.py    # Task operations
├── alembic/                   # Database migrations
│   ├── versions/              # Migration files
│   └── env.py                 # Alembic environment
├── data/                      # Database files
│   └── tasks.db              # SQLite database
├── alembic.ini               # Alembic configuration
├── pyproject.toml            # Dependencies
├── .env.example              # Environment variables template
└── .env                      # Local environment (create from .env.example)
```

## Quick Start

### 1. Setup Environment
```bash
cd backend

# Install dependencies
uv sync --dev

# Copy environment template and customize if needed
cp .env.example .env
```

### 2. Run Server
```bash
# Start development server with auto-reload
uv run uvicorn app.main:app --reload

# Server runs on http://localhost:8000
# API endpoints are at http://localhost:8000/api/v1/tasks
```

### 3. View API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints (v1)

**All endpoints are prefixed with `/api/v1`**

- `GET /api/v1/tasks` - List all tasks
- `GET /api/v1/tasks/{task_id}` - Get a specific task
- `POST /api/v1/tasks` - Create a new task
- `PUT /api/v1/tasks/{task_id}` - Update a task
- `DELETE /api/v1/tasks/{task_id}` - Delete a task

## Testing

```bash
# Run all tests
uv run pytest

# Verbose output
uv run pytest -v

# With coverage report
uv run pytest --cov=app --cov-report=term-missing
```

**Test Coverage:** 96%

## Database Migrations

This project uses Alembic for database schema versioning.

```bash
# Create a new migration after model changes
uv run alembic revision --autogenerate -m "Description of changes"

# Apply migrations
uv run alembic upgrade head

# Rollback one migration
uv run alembic downgrade -1

# View migration history
uv run alembic history
```

## Configuration

Configuration is managed via environment variables (loaded from `.env` file):

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./data/tasks.db` | Database connection string |
| `API_V1_PREFIX` | `/api/v1` | API version prefix |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `DATABASE_ECHO` | `false` | Echo SQL queries (for debugging) |
| `POOL_SIZE` | `5` | SQLAlchemy connection pool size |

See `.env.example` for all available options.

## Architecture

### Layered Design

1. **Routes (`app/main.py`)** - FastAPI endpoints, request/response handling
2. **Services (`app/services/`)** - Business logic, separated from HTTP layer
3. **Database (`app/database.py`)** - SQLAlchemy models and session management
4. **Schemas (`app/schemas.py`)** - Pydantic models for validation

### Key Features

- **API Versioning** - All routes prefixed with `/api/v1` for future compatibility
- **Structured Logging** - Request/response logging with timing
- **Connection Pooling** - Optimized database connections with configurable pool
- **Input Validation** - Pydantic schemas with max length constraints
- **Database Migrations** - Alembic for schema versioning
- **Clean Architecture** - Separated concerns (routes → services → database)

## Development

### Adding New Features

1. **Update Models** - Modify `app/database.py` if schema changes needed
2. **Create Migration** - Run `alembic revision --autogenerate`
3. **Update Service Layer** - Add business logic to `app/services/`
4. **Add Routes** - Create endpoints in `app/main.py`
5. **Write Tests** - Add tests to `app/test_main.py`
6. **Run Tests** - Verify with `uv run pytest`

### Code Style

- Follow existing patterns in the codebase
- Use type hints for all function parameters and returns
- Add docstrings to public functions
- Keep functions small and focused
- Write tests for all new features

## Troubleshooting

**Database locked error:**
- SQLite doesn't handle high concurrency well
- Consider PostgreSQL for production

**Import errors:**
- Ensure you're in the `backend/` directory
- Run `uv sync --dev` to install dependencies

**Migration conflicts:**
- Check `alembic/versions/` for conflicting migrations
- Use `alembic history` to view migration chain
