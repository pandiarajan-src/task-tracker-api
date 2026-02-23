# Input Validation & Sanitization

This document describes the comprehensive input validation and sanitization system implemented in the Task Tracker API.

## Overview

The API implements a **three-layer security model** for input validation:

1. **Request Middleware** - Validates HTTP request structure
2. **Pydantic Schemas** - Validates data types and formats  
3. **Custom Validators** - Sanitizes and checks for security threats

## Features

### 1. Request-Level Validation (`app/middleware/validation.py`)

**Request Size Limiting:**
- Maximum request body size: 1MB (configurable via `MAX_REQUEST_SIZE`)
- Prevents denial-of-service attacks from large payloads
- Returns `413 Request Entity Too Large` for oversized requests

**Content-Type Enforcement:**
- POST, PUT, PATCH requests must use `Content-Type: application/json`
- Returns `415 Unsupported Media Type` for incorrect content types
- Skips validation for GET, DELETE, and documentation endpoints

### 2. Input Sanitization (`app/utils/sanitizer.py`)

**HTML Sanitization:**
```python
sanitize_html("<script>alert('xss')</script>")
# Returns: "alert('xss')"
```
- Strips ALL HTML tags using the `bleach` library
- Prevents XSS (Cross-Site Scripting) attacks
- Configurable via `ENABLE_HTML_SANITIZATION=true`

**SQL Injection Detection:**
```python
check_sql_injection("'; DROP TABLE tasks;--")
# Returns: True (detected)
```
- Detects common SQL injection patterns:
  - `SELECT ... FROM`, `DROP TABLE`, `INSERT INTO`, etc.
  - SQL comments: `--`, `/*`, `*/`
  - Boolean tricks: `OR 1=1`, `AND 1=1`
- Case-insensitive pattern matching
- Configurable via `ENABLE_SQL_SANITIZATION=true`

**Whitespace Normalization:**
```python
sanitize_string("  multiple    spaces  ")
# Returns: "multiple spaces"
```
- Collapses multiple spaces into single space
- Strips leading/trailing whitespace
- Preserves single spaces between words

**Forbidden Words:**
- Configurable word blacklist via `FORBIDDEN_WORDS` environment variable
- Comma-separated list: `FORBIDDEN_WORDS=spam,badword,blocked`
- Case-insensitive matching

### 3. Field Validators (`app/schemas.py`)

Applied to all `TaskCreate` and `TaskUpdate` schemas:

**Title Validation:**
1. Sanitizes HTML and whitespace
2. Rejects if HTML tags were present in original input
3. Checks for SQL injection patterns
4. Blocks dangerous characters: `< > { } [ ]`
5. Checks against forbidden words list

**Description Validation:**
- Same checks as title validation
- Optional field (can be None)

## Configuration

All settings are configured via environment variables in `.env`:

```bash
# Validation Settings
MAX_REQUEST_SIZE=1048576          # 1MB max request size
ENABLE_HTML_SANITIZATION=true    # Strip HTML tags
ENABLE_SQL_SANITIZATION=true     # Check for SQL injection
FORBIDDEN_WORDS=spam,test         # Comma-separated blacklist
VALIDATION_LOG_ENABLED=true      # Log validation events
```

## Error Responses

### 422 Validation Error (Invalid Input)
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "title"],
      "msg": "Title contains forbidden HTML tags or special characters",
      "input": "<script>alert('xss')</script>"
    }
  ]
}
```

### 413 Request Too Large
```json
{
  "detail": "Request body too large. Maximum size: 1MB"
}
```

### 415 Unsupported Media Type
```json
{
  "detail": "Content-Type must be application/json",
  "received": "text/plain"
}
```

## Examples

### ✅ Valid Request
```bash
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Buy groceries", "description": "Milk, eggs, bread"}'

# Response: 201 Created
{
  "id": 1,
  "title": "Buy groceries",
  "description": "Milk, eggs, bread",
  "completed": false,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### ❌ HTML Injection Blocked
```bash
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "<script>alert(\"xss\")</script>"}'

# Response: 422 Unprocessable Entity
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "title"],
      "msg": "Title contains forbidden HTML tags or special characters"
    }
  ]
}
```

### ❌ SQL Injection Blocked
```bash
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Test'"'"'; DROP TABLE tasks;--"}'

# Response: 422 Unprocessable Entity
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "title"],
      "msg": "Title contains invalid characters or patterns"
    }
  ]
}
```

### ❌ Wrong Content-Type
```bash
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: text/plain" \
  -d 'title=Test'

# Response: 415 Unsupported Media Type
{
  "detail": "Content-Type must be application/json",
  "received": "text/plain"
}
```

## Testing

### Run Validation Tests
```bash
# All tests
uv run pytest app/test_main.py app/test_validation.py -v

# Just validation tests
uv run pytest app/test_validation.py -v

# With coverage
uv run pytest --cov=app --cov-report=term-missing
```

### Test Coverage
- Request middleware: 83%
- Sanitization utilities: 56%
- Schema validators: 71%
- Overall: 88%

## Security Best Practices

1. **Defense in Depth**: Multiple validation layers provide redundancy
2. **Fail Secure**: Invalid input is rejected, not sanitized and accepted
3. **Clear Errors**: Validation errors are specific and helpful
4. **Logging**: All validation failures are logged for monitoring
5. **Configurable**: Security settings can be tuned for your environment

## Logging

When `VALIDATION_LOG_ENABLED=true`, the following events are logged:

- HTML content sanitized
- SQL injection patterns detected
- Forbidden words found
- Oversized requests rejected
- Wrong content-type requests

Example log entries:
```
WARNING: HTML content sanitized: '<script>...' -> 'script...'
WARNING: Potential SQL injection detected: Test'; DROP TABLE
INFO: Request rejected: body size 2MB exceeds limit 1MB
INFO: Request rejected: content-type text/plain, expected application/json
```

## Performance

- **Request overhead**: < 1ms per request
- **Sanitization overhead**: < 0.1ms per field
- **Memory usage**: Minimal (no buffering of large payloads)

## Future Enhancements

Potential improvements (not yet implemented):

- [ ] Rate limiting per IP address
- [ ] Custom error codes for different validation failures
- [ ] Validation metrics dashboard
- [ ] Configurable per-endpoint validation rules
- [ ] Advanced SQL injection detection (context-aware)
- [ ] OWASP compliance validation

## References

- [OWASP Input Validation Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html)
- [FastAPI Middleware](https://fastapi.tiangolo.com/tutorial/middleware/)
- [Pydantic Validators](https://docs.pydantic.dev/latest/concepts/validators/)
- [bleach Documentation](https://bleach.readthedocs.io/)
