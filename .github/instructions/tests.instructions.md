---
applyTo: "**/*.test.ts,**/*test*.py"
---

## Frontend Testing (Jest)
- Use Jest with describe/it blocks
- Each test file must have at least one happy path and one error case
- Use meaningful test names: "should [expected behavior] when [condition]"
- Mock external dependencies and API calls
- Test files should follow pattern: `*.test.ts` or `*.test.tsx`

## Backend Testing (Pytest)
- Use pytest with clear function names: `test_[action]_[condition]_[expected_result]`
- Each test module must have at least one happy path and one error case
- Use pytest fixtures for setup and teardown
- Mock external dependencies and database calls
- Test files should follow pattern: `test_*.py` or `*_test.py`

## General Testing Guidelines
- Aim for high coverage but prioritize meaningful tests over 100% coverage
- Run tests frequently during development to catch issues early
- Write tests first when adding new features
- Mock external dependencies and API calls

```bash
# Run frontend tests
cd frontend
npm test
```
```bash
# Run backend tests
cd backend
uv run pytest
```
