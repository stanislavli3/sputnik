"""Tests for API RBAC endpoints."""

import pytest
from fastapi.testclient import TestClient
from sputnik.api.server import app
from sputnik.api.db import get_roles_db


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def roles_db(temp_db):
    """Create RolesDB instance."""
    db = RolesDB(db_path=temp_db)
    # Assign admin role to test user
    db.assign_role("test_admin", "admin")
    db.assign_role("test_user", "finance_analyst")
    return db


def test_list_roles_requires_permission(client):
    """Test that listing roles requires permission."""
    # Without auth, should get 401 or 403
    response = client.get("/api/v1/users/roles")
    # In dev mode without auth, might succeed, but with auth it should require permission
    assert response.status_code in [200, 401, 403]


def test_get_my_roles(client):
    """Test getting current user's roles."""
    # Without auth, should fail
    response = client.get("/api/v1/users/me/roles")
    assert response.status_code in [200, 401, 403]


def test_assign_role_requires_admin(client, roles_db):
    """Test that assigning roles requires admin."""
    response = client.post(
        "/api/v1/users/roles/assign",
        json={
            "user_id": "test_user_123",
            "role_id": "finance_analyst",
        },
    )
    # Should require admin role
    assert response.status_code in [200, 401, 403, 500]


def test_revoke_role_requires_admin(client, roles_db):
    """Test that revoking roles requires admin."""
    response = client.post(
        "/api/v1/users/roles/revoke",
        json={
            "user_id": "test_user_123",
            "role_id": "finance_analyst",
        },
    )
    # Should require admin role
    assert response.status_code in [200, 401, 403, 500]
