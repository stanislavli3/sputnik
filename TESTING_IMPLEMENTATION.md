# Testing Implementation

## Overview

Comprehensive test suite for RBAC, session management, and audit logging features.

## Test Structure

### Unit Tests

- **`test_rbac.py`**: Tests for role-based access control
  - Role assignment/revocation
  - Permission checking
  - Wildcard permissions
  - Multiple roles per user

- **`test_sessions.py`**: Tests for session management
  - Session creation
  - Activity updates
  - Session deactivation
  - Expiration handling
  - Concurrent session limits

- **`test_audit.py`**: Tests for audit logging
  - Log creation
  - Filtering by user/action/resource
  - Pagination

### API Tests

- **`test_api_rbac.py`**: API endpoint tests for RBAC
- **`test_api_sessions.py`**: API endpoint tests for sessions
- **`test_api_audit.py`**: API endpoint tests for audit logs
- **`test_api_query.py`**: API endpoint tests for queries
- **`test_api_reviews.py`**: API endpoint tests for reviews

### Integration Tests

- **`test_integration_rbac.py`**: End-to-end RBAC workflow tests

## Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_rbac.py

# Run with verbose output
pytest tests/ -v

# Run with coverage (if pytest-cov installed)
pytest tests/ --cov=sputnik --cov-report=html
```

## Test Configuration

Tests use temporary DuckDB databases created per test. The `SKIP_DEFAULT_ROLES` environment variable is set to avoid pandas import issues during initialization.

## Fixtures

- `temp_db`: Creates temporary database path
- `roles_db`: Creates RolesDB instance with test database
- `sessions_db`: Creates SessionsDB instance with test database
- `audit_db`: Creates AuditLogDB instance with test database
- `mock_user`: Mock user data
- `admin_user`: Mock admin user data
- `mock_request`: Mock FastAPI request

## Known Issues

- Bus error when importing pandas in test environment (workaround: SKIP_DEFAULT_ROLES=true)
- Some API tests require authentication mocking (currently skipped or return 401/403)

## Coverage Goals

- Unit tests: 80%+ coverage for RBAC, sessions, audit
- Integration tests: Critical workflows covered
- API tests: All endpoints have basic tests
