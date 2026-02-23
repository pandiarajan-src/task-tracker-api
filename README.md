# Task Tracker API

A **production-ready** task management API built with FastAPI, featuring clean architecture, comprehensive security, database migrations, and 96%+ test coverage.

## 🚀 Features

- ✅ **RESTful API** with full CRUD operations
- ✅ **Enterprise Security** - 3-layer input validation (XSS, SQL injection protection)
- ✅ **Clean Architecture** - Layered design (routes → services → database)
- ✅ **Database Migrations** - Alembic for schema versioning
- ✅ **96%+ Test Coverage** - Comprehensive pytest suite
- ✅ **API Versioning** - `/api/v1` prefix for backward compatibility
- ✅ **Rate Limiting** - 100 requests/minute per IP
- ✅ **Structured Logging** - Production-ready monitoring
- ✅ **Docker Ready** - Containerized deployment
- ✅ **CI/CD Pipeline** - Automated testing with GitHub Actions

## 🔒 Security (NEW!)

The API includes **enterprise-grade input validation**:

- **XSS Prevention**: Blocks HTML tags like `<script>alert('xss')</script>`
- **SQL Injection Protection**: Detects patterns like `'; DROP TABLE`
- **Content-Type Enforcement**: JSON-only endpoints (returns 415 otherwise)
- **Request Size Limits**: 1MB maximum payload (configurable)
- **Input Sanitization**: Automatic whitespace normalization
- **Dangerous Character Blocking**: Rejects `<>{}[]` in user input

📖 **See [VALIDATION.md](backend/VALIDATION.md) for complete security documentation**

## 🚀 Quick Start

### Development Setup
```bash
# Clone and setup
git clone <repository-url>
cd task-tracker-api

# Complete setup with one command
make dev-setup

# Or manually:
cd backend
uv sync --dev
cp .env.example .env
```

### Run the Server
```bash
# Using Makefile (recommended)
make run

# Or directly with uv
cd backend && uv run uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000

### API Documentation
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## 📋 API Endpoints (v1)

**All endpoints are prefixed with `/api/v1`**

- **GET /api/v1/tasks** - List all tasks with pagination
- **GET /api/v1/tasks/{task_id}** - Get a specific task
- **POST /api/v1/tasks** - Create a new task
- **PUT /api/v1/tasks/{task_id}** - Update a task (partial updates supported)
- **DELETE /api/v1/tasks/{task_id}** - Delete a task

### Example Usage

```bash
# Create a task
curl -X POST "http://localhost:8000/api/v1/tasks" \
     -H "Content-Type: application/json" \
     -d '{"title": "Buy groceries", "description": "Milk, bread, eggs"}'

# Get all tasks
curl "http://localhost:8000/api/v1/tasks"

# Update a task
curl -X PUT "http://localhost:8000/api/v1/tasks/1" \
     -H "Content-Type: application/json" \
     -d '{"completed": true}'

# Delete a task
curl -X DELETE "http://localhost:8000/api/v1/tasks/1"
```

## 🧪 Testing

```bash
# Using Makefile
make test              # With coverage
make test-quick        # Without coverage
make check-all         # Lint + format + test

# Or directly
cd backend
uv run pytest app/test_main.py -v --cov=app
```

**Test Results:** ✅ 13/13 tests passed | 📊 96% coverage

## 🛠️ Development Commands

```bash
make help              # Show all available commands
make install           # Install dependencies
make run               # Run development server
make test              # Run tests with coverage
make lint              # Run linter
make format            # Format code
make migrate           # Run database migrations
make clean             # Clean generated files
```

## 📁 Project Structure

```
task-tracker-api/
├── .github/
│   └── workflows/
│       └── backend-tests.yml  # CI/CD pipeline
├── backend/
│   ├── app/                   # Application package
│   │   ├── config.py          # Configuration management
│   │   ├── database.py        # SQLAlchemy models
│   │   ├── schemas.py         # Pydantic validation
│   │   ├── main.py            # FastAPI routes
│   │   ├── test_main.py       # Test suite
│   │   └── services/          # Business logic layer
│   │       └── task_service.py
│   ├── alembic/               # Database migrations
│   ├── data/                  # Database files
│   ├── .env.example           # Environment template
│   └── pyproject.toml         # Dependencies
├── Dockerfile                 # Container definition
├── docker-compose.yml         # Docker orchestration
├── Makefile                   # Development commands
└── README.md                  # This file
```

## 🛠️ Technology Stack

- **Backend:** FastAPI, SQLAlchemy, Pydantic
- **Database:** SQLite (with Alembic migrations)
- **Testing:** pytest, httpx (96% coverage)
- **Linting:** Ruff (fast Python linter/formatter)
- **Package Management:** uv
- **Containerization:** Docker, Docker Compose

## 📊 Features

### ✅ Core Features

- **CRUD Operations** - Complete Create, Read, Update, Delete functionality
- **API Versioning** - `/api/v1` prefix for backward compatibility
- **Clean Architecture** - Layered design (routes → services → database)
- **Database Migrations** - Alembic for schema versioning
- **Connection Pooling** - Optimized database connections
- **Structured Logging** - Request/response logging with timing
- **Input Validation** - Pydantic schemas with length constraints
- **Comprehensive Testing** - 96% code coverage with pytest
- **Environment Config** - Settings via .env files
- **Auto Documentation** - Interactive API docs with Swagger/ReDoc

### 🔒 Security & Production

- **CORS Middleware** - Configurable cross-origin resource sharing
- **Rate Limiting** - Protect API from abuse (100 req/min default)
- **Input Sanitization** - Max length validation on all fields
- **Environment-based Config** - Separate dev/prod settings

### 🚀 Developer Experience

- **Makefile** - Simple commands for common tasks
- **Docker Support** - Containerized deployment ready
- **Pre-commit Hooks** - Automated code quality checks
- **GitHub Actions** - Automated testing on PR/push
- **Hot Reload** - Auto-restart on code changes

## 🐳 Docker Deployment

```bash
# Build and run with docker-compose
docker-compose up -d

# Or build manually
docker build -t task-tracker-api .
docker run -p 8000:8000 task-tracker-api
```

## 🔧 Configuration

Key environment variables (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./data/tasks.db` | Database connection |
| `API_V1_PREFIX` | `/api/v1` | API version prefix |
| `LOG_LEVEL` | `INFO` | Logging level |
| `RATE_LIMIT_ENABLED` | `true` | Enable rate limiting |
| `RATE_LIMIT_TIMES` | `100` | Requests per window |
| `CORS_ORIGINS` | `localhost:3000,...` | Allowed origins |

## 📝 Development

See [backend/README.md](backend/README.md) for detailed development documentation including:
- Database migration guide
- Configuration options
- Adding new features
- Troubleshooting tips

## 🎯 Next Steps

1. **Frontend** - Add React/TypeScript UI
2. **Authentication** - JWT-based user authentication
3. **Advanced Features** - Task categories, due dates, priorities, tags
4. **PostgreSQL** - Replace SQLite for production
5. **Redis** - Add caching layer
6. **Observability** - Metrics and distributed tracing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests (`make test`)
4. Format code (`make format`)
5. Commit changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📄 License

This project is open source and available under the MIT License.