# Task Tracker Project

A simple task tracker API built with FastAPI and SQLite, following clean architecture principles with comprehensive testing.

## Code Style

**Naming Conventions:**
- Variables/functions: `camelCase` (JS) or `snake_case` (Python)
- Classes: `PascalCase` (`TaskCreate`, `TaskResponse`)
- Files: `snake_case` (`test_main.py`, `task_id`)
- Components: `PascalCase` (React components when added)

**Key Patterns from Codebase:**
- See [main.py](backend/main.py) for FastAPI route structure
- See [schemas.py](backend/schemas.py) for Pydantic inheritance pattern
- See [test_main.py](backend/test_main.py) for test naming: `test_[action]_[condition]_[expected_result]`

## Architecture

**Backend Structure (FastAPI + SQLAlchemy):**
```
backend/
├── main.py          # FastAPI app with CRUD routes
├── database.py      # SQLAlchemy models + session management  
├── schemas.py       # Pydantic request/response models
└── test_main.py     # Comprehensive pytest suite
```

**Key Patterns:**
- **Database**: SQLite with SQLAlchemy ORM, timezone-aware timestamps
- **API Design**: RESTful CRUD with dependency injection: `db: Session = Depends(get_db)`
- **Validation**: Pydantic schemas with inheritance (`TaskBase` → `TaskCreate`/`TaskUpdate`)
- **Updates**: Partial updates using `model_dump(exclude_unset=True)`

## Build and Test

**Setup:**
```bash
cd backend
uv sync --dev
```

**Run Server:**
```bash
uv run uvicorn main:app --reload
```

**Testing (ALWAYS run before claiming code works):**
```bash
uv run pytest              # Basic tests
uv run pytest -v          # Verbose output  
uv run pytest --cov       # With coverage (96% target)
```

## Project Conventions

**Database Models** (see [database.py](backend/database.py)):
- Use `Base = declarative_base()`
- Auto-timestamps: `created_at`, `updated_at` with `datetime.now(timezone.utc)`
- Primary keys with `index=True`

**FastAPI Routes** (see [main.py](backend/main.py)):
```python
@app.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
```

**Testing** (see [test_main.py](backend/test_main.py)):
- Each endpoint needs happy path AND error case tests
- Use `TestClient` with database override
- Fixture pattern for database cleanup

**Error Handling:**
- HTTPException with specific messages: `f"Task with id {task_id} not found"`
- Proper HTTP status codes (404, 422, 201, etc.)

## Integration Points

**Database:** SQLite with connection string `sqlite:///./tasks.db`
**API Docs:** Auto-generated at `http://localhost:8000/docs`

## Security

**Input Validation:** All requests validated through Pydantic schemas
**Database:** Use parameterized queries via SQLAlchemy (prevents SQL injection)

---

## Critical Rules

- **Use `uv` exclusively** - never `pip` or `python` directly
- **Test everything** - run `uv run pytest` before claiming features work  
- **Follow existing patterns** - maintain consistency with [main.py](backend/main.py) structure
- **Keep it simple** - avoid over-engineering, focus on core functionality
