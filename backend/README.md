# Task Tracker API Backend

A RESTful API for managing tasks built with FastAPI and SQLAlchemy.

## Features

- **GET /tasks** - List all tasks with optional pagination
- **GET /tasks/{task_id}** - Get a specific task by ID
- **POST /tasks** - Create a new task
- **PUT /tasks/{task_id}** - Update an existing task
- **DELETE /tasks/{task_id}** - Delete a task

## Quick Start

1. Install dependencies:
```bash
uv sync --dev
```

2. Run the development server:
```bash
uv run uvicorn main:app --reload
```

3. View API documentation at http://localhost:8000/docs

## Testing

Run the test suite:
```bash
uv run pytest
```

Run tests with coverage:
```bash
uv run pytest --cov=.
```

## API Usage Examples

### Create a Task
```bash
curl -X POST "http://localhost:8000/tasks" \
     -H "Content-Type: application/json" \
     -d '{"title": "Buy groceries", "description": "Milk, bread, eggs"}'
```

### Get All Tasks
```bash
curl "http://localhost:8000/tasks"
```

### Update a Task
```bash
curl -X PUT "http://localhost:8000/tasks/1" \
     -H "Content-Type: application/json" \
     -d '{"completed": true}'
```

### Delete a Task
```bash
curl -X DELETE "http://localhost:8000/tasks/1"
```

## Task Schema

### TaskCreate/TaskUpdate
```json
{
  "title": "string (required for create)",
  "description": "string (optional)",
  "completed": "boolean (optional, defaults to false)"
}
```

### TaskResponse
```json
{
  "id": "integer",
  "title": "string",
  "description": "string",
  "completed": "boolean",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```