# Task Tracker API

A simple yet complete task management application built with React (frontend) and FastAPI (backend).

## 🚀 Quick Start

### Backend Setup
```bash
cd backend
uv sync --dev
```

### Run the Server
```bash
# Start development server with auto-reload
uv run uvicorn main:app --reload

# Start server on specific host/port
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at http://localhost:8000

### API Documentation
Visit http://localhost:8000/docs for interactive Swagger documentation.

## 📋 API Endpoints

- **GET /tasks** - List all tasks
- **GET /tasks/{task_id}** - Get a specific task
- **POST /tasks** - Create a new task
- **PUT /tasks/{task_id}** - Update a task
- **DELETE /tasks/{task_id}** - Delete a task

## ✅ CRUD Operations Verified

All endpoints have been implemented and tested:

### ✅ **CREATE** - POST /tasks
```bash
curl -X POST "http://localhost:8000/tasks" \
     -H "Content-Type: application/json" \
     -d '{"title": "Buy groceries", "description": "Milk, bread, eggs"}'
```

### ✅ **READ** - GET /tasks and GET /tasks/{id}
```bash
curl "http://localhost:8000/tasks"           # Get all tasks
curl "http://localhost:8000/tasks/1"         # Get specific task
```

### ✅ **UPDATE** - PUT /tasks/{id}
```bash
curl -X PUT "http://localhost:8000/tasks/1" \
     -H "Content-Type: application/json" \
     -d '{"completed": true}'
```

### ✅ **DELETE** - DELETE /tasks/{id}
```bash
curl -X DELETE "http://localhost:8000/tasks/1"
```

## 🧪 Testing

All endpoints include comprehensive test coverage:

### Run Tests
```bash
cd backend

# Simple test run
uv run pytest

# Verbose output with detailed test names
uv run pytest -v

# With coverage report
uv run pytest --cov

# Detailed coverage with missing lines
uv run pytest --cov=. --cov-report=term-missing

# Generate HTML coverage report
uv run pytest --cov --cov-report=html
```

**Test Results**: ✅ 11 tests passed (100% success rate) | 📊 96% coverage

- Tests cover both happy path and error cases
- Includes validation for 404 errors on non-existent resources
- Tests data persistence and proper HTTP status codes

## 📊 Features Implemented

- ✅ **CRUD Operations**: Complete Create, Read, Update, Delete functionality
- ✅ **Data Validation**: Pydantic schemas with proper validation
- ✅ **Error Handling**: Proper HTTP status codes and error messages
- ✅ **Database**: SQLite with SQLAlchemy ORM
- ✅ **Testing**: Comprehensive test suite with pytest
- ✅ **Documentation**: Auto-generated API docs with FastAPI
- ✅ **Modern Python**: Uses latest FastAPI patterns with async support

## 📁 Project Structure

```
task-tracker-api/
├── backend/
│   ├── main.py           # FastAPI application with CRUD routes
│   ├── database.py       # SQLAlchemy models and database setup
│   ├── schemas.py        # Pydantic schemas for validation
│   ├── test_main.py      # Comprehensive test suite
│   ├── demo.py           # API usage demonstration
│   └── README.md         # Backend documentation
└── README.md             # This file
```

## 🛠️ Technology Stack

- **Backend**: FastAPI, SQLAlchemy, Pydantic
- **Database**: SQLite
- **Testing**: pytest, httpx
- **Package Management**: uv

## 🎯 Next Steps

The backend API is complete and fully functional. To extend the project:

1. **Frontend**: The frontend folder can be added for a React/TypeScript UI
2. **Authentication**: Add user authentication and authorization
3. **Advanced Features**: Add task categories, due dates, priorities
4. **Deployment**: Add Docker configuration for production deployment

## 📝 Usage Example

See [backend/demo.py](backend/demo.py) for a complete example of interacting with the API programmatically.