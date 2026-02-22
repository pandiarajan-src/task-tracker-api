# Task Tracker Project

This project is a simple task tracker application built with React and FastAPI. It allows users to create, edit, and delete tasks, as well as mark them as completed. The application uses a RESTful API to manage tasks on the backend, and it is designed to be responsive and user-friendly.

## Features
- Create, edit, and delete tasks
- Mark tasks as completed
- Responsive design for mobile and desktop
- RESTful API for backend management

## Technologies Used
- Frontend: React, TypeScript, CSS
- Backend: FastAPI, Python
- Package Management: uv (Python)
- Database: SQLite
- Testing: Jest, Pytest

## Installation
1. Clone the repository:
```bash
git clone <repository-url>
```
2. Navigate to the project directory:
```bash
cd task-tracker-api
```
3. Install frontend dependencies:
```bash
cd frontend
npm install
```
4. Install backend dependencies:
```bash
cd ../backend
uv sync
```
5. Run the backend server:
```bash
uv run uvicorn main:app --reload
```
6. Run the frontend development server:
```bash
cd ../frontend
npm start
```

## Development Principles
This is a simple task tracker focused on core functionality. The frontend uses React/TypeScript and the backend uses FastAPI with SQLite. Keep the codebase maintainable and well-tested.

## Coding Standards
- Use camelCase for variable and function names
- Use PascalCase for component names in React
- Keep functions small and focused on a single task
- Use descriptive names for variables and functions
- Avoid magic numbers; use constants with descriptive names
- Use latest versions of libraries and idiomatic approaches
- Keep it simple - NEVER over-engineer, ALWAYS simplify
- Use uv for all Python package management and script execution - never use pip or python directly
- **TESTING REQUIRED**: All features must be thoroughly tested and validated before claiming they work
- Write tests first when adding new features
- Run full test suite before any commits

## Testing
Run tests before claiming any feature is working:
```bash
# Frontend tests
cd frontend
npm test

# Backend tests  
cd backend
uv run pytest
```

## Contributing
Contributions welcome! Requirements:
1. Follow coding standards above
2. **Include tests for all new features or bug fixes**
3. Ensure all existing tests pass
4. Keep changes focused and simple
