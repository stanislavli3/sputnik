"""Tests for RBAC functionality."""

import pytest
import os
from sputnik.api.rbac import (
    get_user_permissions,
    get_user_roles,
    has_permission,
    has_role,
)
from sputnik.api.db import RolesDB


@pytest.fixture
def roles_db(temp_db, monkeypatch):
    """Create RolesDB instance with test database."""
    # Temporarily override the global instance
    from sputnik.api import db as db_module
    original_get_roles_db = db_module.get_roles_db
    
    def get_test_roles_db():
        return RolesDB(db_path=temp_db)
    
    monkeypatch.setattr(db_module, "get_roles_db", get_test_roles_db)
    
    db = RolesDB(db_path=temp_db)
    return db


def test_get_user_roles_no_user(roles_db):
    """Test getting roles for non-existent user."""
    roles = get_user_roles(None)
    assert roles == []


def test_get_user_permissions_no_user(roles_db):
    """Test getting permissions for non-existent user."""
    permissions = get_user_permissions(None)
    assert permissions == []


def test_assign_role(roles_db, monkeypatch):
    """Test assigning a role to a user."""
    import json
    from sputnik.api import rbac as rbac_module
    
    # Create a test role directly (avoiding pandas import issue)
    conn = roles_db._get_connection()
    try:
        conn.execute("""
            INSERT OR IGNORE INTO roles (id, name, description, permissions)
            VALUES (?, ?, ?, ?)
        """, ("finance_analyst", "Finance Analyst", "Test role", json.dumps(["query:execute"])))
        conn.commit()
    finally:
        conn.close()
    
    # Patch get_roles_db to return our test instance
    monkeypatch.setattr(rbac_module, "get_roles_db", lambda: roles_db)
    
    success = roles_db.assign_role(
        user_id="test_user_123",
        role_id="finance_analyst",
        assigned_by="admin_user_123",
    )
    assert success is True
    
    # Verify role was assigned
    roles = roles_db.get_user_roles("test_user_123")
    assert "finance_analyst" in roles


def test_revoke_role(roles_db, monkeypatch):
    """Test revoking a role from a user."""
    from sputnik.api import rbac as rbac_module
    monkeypatch.setattr(rbac_module, "get_roles_db", lambda: roles_db)
    
    # First assign a role
    roles_db.assign_role("test_user_123", "finance_analyst")
    
    # Then revoke it
    success = roles_db.revoke_role("test_user_123", "finance_analyst")
    assert success is True
    
    # Verify role was revoked
    roles = roles_db.get_user_roles("test_user_123")
    assert "finance_analyst" not in roles


def test_get_user_permissions(roles_db, monkeypatch):
    """Test getting permissions for a user."""
    import json
    from sputnik.api import rbac as rbac_module
    
    # Create a test role with permissions
    conn = roles_db._get_connection()
    try:
        conn.execute("""
            INSERT OR IGNORE INTO roles (id, name, description, permissions)
            VALUES (?, ?, ?, ?)
        """, ("finance_analyst", "Finance Analyst", "Test", json.dumps(["query:execute", "query:view_history", "query:export"])))
        conn.commit()
    finally:
        conn.close()
    
    # Patch get_roles_db
    monkeypatch.setattr(rbac_module, "get_roles_db", lambda: roles_db)
    
    # Assign finance_analyst role
    roles_db.assign_role("test_user_123", "finance_analyst")
    
    permissions = roles_db.get_user_permissions("test_user_123")
    assert "query:execute" in permissions
    assert "query:view_history" in permissions
    assert "query:export" in permissions


def test_admin_has_all_permissions(roles_db, monkeypatch):
    """Test that admin role has all permissions."""
    from sputnik.api import rbac as rbac_module
    monkeypatch.setattr(rbac_module, "get_roles_db", lambda: roles_db)
    
    roles_db.assign_role("admin_user_123", "admin")
    
    permissions = roles_db.get_user_permissions("admin_user_123")
    assert "*" in permissions or len(permissions) > 10  # Admin should have many permissions


def test_has_permission(roles_db, monkeypatch):
    """Test has_permission function."""
    from sputnik.api import rbac as rbac_module
    monkeypatch.setattr(rbac_module, "get_roles_db", lambda: roles_db)
    
    roles_db.assign_role("test_user_123", "finance_analyst")
    
    assert has_permission("test_user_123", "query:execute") is True
    assert has_permission("test_user_123", "reviews:approve") is False
    assert has_permission("test_user_123", "nonexistent:permission") is False


def test_has_role(roles_db, monkeypatch):
    """Test has_role function."""
    from sputnik.api import rbac as rbac_module
    monkeypatch.setattr(rbac_module, "get_roles_db", lambda: roles_db)
    
    roles_db.assign_role("test_user_123", "finance_analyst")
    
    assert has_role("test_user_123", "finance_analyst") is True
    assert has_role("test_user_123", "admin") is False
    assert has_role("test_user_123", "nonexistent_role") is False


def test_wildcard_permissions(roles_db, monkeypatch):
    """Test wildcard permission matching."""
    from sputnik.api import rbac as rbac_module
    monkeypatch.setattr(rbac_module, "get_roles_db", lambda: roles_db)
    
    # Create a custom role with wildcard permission
    import json
    import duckdb
    
    conn = duckdb.connect(roles_db.db_path)
    conn.execute("""
        INSERT INTO roles (id, name, description, permissions)
        VALUES (?, ?, ?, ?)
    """, ("custom_role", "Custom Role", "Test role", json.dumps(["query:*"])))
    conn.close()
    
    roles_db.assign_role("test_user_123", "custom_role")
    
    # Should match query:execute, query:view_history, etc.
    assert has_permission("test_user_123", "query:execute") is True
    assert has_permission("test_user_123", "query:view_history") is True
    assert has_permission("test_user_123", "reviews:approve") is False


def test_multiple_roles(roles_db, monkeypatch):
    """Test user with multiple roles."""
    from sputnik.api import rbac as rbac_module
    monkeypatch.setattr(rbac_module, "get_roles_db", lambda: roles_db)
    
    roles_db.assign_role("test_user_123", "finance_analyst")
    roles_db.assign_role("test_user_123", "expert_reviewer")
    
    roles = roles_db.get_user_roles("test_user_123")
    assert "finance_analyst" in roles
    assert "expert_reviewer" in roles
    
    # Should have permissions from both roles
    permissions = roles_db.get_user_permissions("test_user_123")
    assert "query:execute" in permissions  # From finance_analyst
    assert "reviews:approve" in permissions  # From expert_reviewer
