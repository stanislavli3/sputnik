"""Pytest configuration and fixtures."""

import os
import tempfile
import pytest
from pathlib import Path

# Set test environment variables
os.environ["ENABLE_AUTH"] = "false"  # Disable auth for tests
os.environ["DEBUG"] = "true"
os.environ["SKIP_DEFAULT_ROLES"] = "true"  # Skip default role initialization in tests


@pytest.fixture
def temp_db():
    """Create a temporary database path for testing."""
    # Don't create the file - DuckDB will create it
    db_path = tempfile.mktemp(suffix=".duckdb")
    
    yield db_path
    
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def mock_user():
    """Mock user for testing."""
    return {
        "user_id": "test_user_123",
        "email": "test@example.com",
        "session_id": "test_session_123",
    }


@pytest.fixture
def admin_user():
    """Mock admin user for testing."""
    return {
        "user_id": "admin_user_123",
        "email": "admin@example.com",
        "session_id": "admin_session_123",
    }


@pytest.fixture
def mock_request(mock_user):
    """Mock FastAPI request with user."""
    from unittest.mock import Mock
    
    request = Mock()
    request.state = Mock()
    request.state.user = mock_user
    request.headers = {}
    request.url.path = "/api/v1/test"
    request.method = "GET"
    request.client = Mock()
    request.client.host = "127.0.0.1"
    return request


@pytest.fixture(autouse=True)
def set_test_env():
    """Automatically set test environment variables."""
    import os
    os.environ["SKIP_DEFAULT_ROLES"] = "true"
    yield
    # Cleanup if needed
    if "SKIP_DEFAULT_ROLES" in os.environ:
        del os.environ["SKIP_DEFAULT_ROLES"]


def init_default_roles_for_test(roles_db):
    """Helper to initialize default roles in tests when needed."""
    import json
    
    # Use RolesDB's connection method to avoid importing duckdb directly
    conn = roles_db._get_connection()
    try:
        default_roles = [
            {
                "id": "admin",
                "name": "Admin",
                "description": "Full system access",
                "permissions": ["*"]
            },
            {
                "id": "finance_analyst",
                "name": "Finance Analyst",
                "description": "Can execute queries and view history",
                "permissions": ["query:execute", "query:view_history", "query:export"]
            },
            {
                "id": "expert_reviewer",
                "name": "Expert Reviewer",
                "description": "Can approve/reject reviews",
                "permissions": ["query:execute", "reviews:approve", "reviews:reject", "reviews:edit"]
            },
            {
                "id": "viewer",
                "name": "Viewer",
                "description": "Read-only access",
                "permissions": ["query:view_history", "metrics:view"]
            }
        ]
        
        for role in default_roles:
            try:
                permissions_json = json.dumps(role["permissions"])
                conn.execute("""
                    INSERT OR IGNORE INTO roles (id, name, description, permissions)
                    VALUES (?, ?, ?, ?)
                """, (role["id"], role["name"], role["description"], permissions_json))
            except:
                pass
        conn.commit()
    finally:
        conn.close()
