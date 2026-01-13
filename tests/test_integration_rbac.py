"""Integration tests for RBAC workflow."""

import pytest
from sputnik.api.db import get_roles_db, RolesDB, get_history_db, QueryHistoryDB
from sputnik.api.rbac import has_permission, has_role


@pytest.fixture
def roles_db(temp_db):
    """Create RolesDB instance."""
    return RolesDB(db_path=temp_db)


@pytest.fixture
def history_db(temp_db):
    """Create QueryHistoryDB instance."""
    return QueryHistoryDB(db_path=temp_db)


def test_finance_analyst_workflow(roles_db, history_db):
    """Test complete workflow for finance analyst role."""
    # Assign finance_analyst role
    roles_db.assign_role("finance_user", "finance_analyst")
    
    # Check permissions
    assert has_permission("finance_user", "query:execute") is True
    assert has_permission("finance_user", "query:view_history") is True
    assert has_permission("finance_user", "query:export") is True
    assert has_permission("finance_user", "reviews:approve") is False
    
    # User should be able to execute queries (permission check passes)
    # In real scenario, this would be checked in the endpoint decorator


def test_expert_reviewer_workflow(roles_db):
    """Test complete workflow for expert reviewer role."""
    # Assign expert_reviewer role
    roles_db.assign_role("expert_user", "expert_reviewer")
    
    # Check permissions
    assert has_permission("expert_user", "query:execute") is True
    assert has_permission("expert_user", "reviews:approve") is True
    assert has_permission("expert_user", "reviews:reject") is True
    assert has_permission("expert_user", "reviews:edit") is True
    assert has_permission("expert_user", "query:export") is False


def test_viewer_limited_access(roles_db):
    """Test that viewer role has limited access."""
    roles_db.assign_role("viewer_user", "viewer")
    
    # Viewer should have read-only permissions
    assert has_permission("viewer_user", "query:view_history") is True
    assert has_permission("viewer_user", "query:execute") is False
    assert has_permission("viewer_user", "reviews:approve") is False


def test_admin_full_access(roles_db):
    """Test that admin has full access."""
    roles_db.assign_role("admin_user", "admin")
    
    # Admin should have all permissions
    permissions = roles_db.get_user_permissions("admin_user")
    assert "*" in permissions or len(permissions) > 10
    
    # Should have permission for everything
    assert has_permission("admin_user", "query:execute") is True
    assert has_permission("admin_user", "reviews:approve") is True
    assert has_permission("admin_user", "roles:assign") is True
    assert has_permission("admin_user", "nonexistent:permission") is True  # Admin has all


def test_role_assignment_workflow(roles_db):
    """Test complete role assignment workflow."""
    # Start with no roles
    assert len(roles_db.get_user_roles("new_user")) == 0
    
    # Assign finance_analyst role
    roles_db.assign_role("new_user", "finance_analyst")
    assert "finance_analyst" in roles_db.get_user_roles("new_user")
    
    # Add expert_reviewer role
    roles_db.assign_role("new_user", "expert_reviewer")
    roles = roles_db.get_user_roles("new_user")
    assert "finance_analyst" in roles
    assert "expert_reviewer" in roles
    
    # Revoke finance_analyst
    roles_db.revoke_role("new_user", "finance_analyst")
    roles = roles_db.get_user_roles("new_user")
    assert "finance_analyst" not in roles
    assert "expert_reviewer" in roles
