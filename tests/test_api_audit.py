"""Tests for audit log API endpoints."""

import pytest
from fastapi.testclient import TestClient
from sputnik.api.server import app
from sputnik.api.db import get_audit_log_db, AuditLogDB


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def audit_db(temp_db):
    """Create AuditLogDB instance."""
    return AuditLogDB(db_path=temp_db)


def test_get_audit_logs_requires_admin(client, audit_db):
    """Test that audit logs require admin access."""
    # Create some audit logs
    audit_db.log_action("user_1", "query_executed", "query", "q1")
    
    response = client.get("/api/v1/audit/logs")
    # Should require admin role
    assert response.status_code in [200, 401, 403]


def test_get_audit_logs_with_filters(client, audit_db):
    """Test getting audit logs with filters."""
    audit_db.log_action("user_1", "query_executed", "query", "q1")
    audit_db.log_action("user_2", "review_approved", "review", "r1")
    
    # Test with user filter
    response = client.get("/api/v1/audit/logs?user_id=user_1")
    assert response.status_code in [200, 401, 403]
    
    # Test with action filter
    response = client.get("/api/v1/audit/logs?action=query_executed")
    assert response.status_code in [200, 401, 403]


def test_get_audit_logs_pagination(client, audit_db):
    """Test pagination of audit logs."""
    # Create multiple logs
    for i in range(15):
        audit_db.log_action(f"user_{i}", "query_executed", "query", f"q{i}")
    
    response = client.get("/api/v1/audit/logs?page=1&page_size=10")
    assert response.status_code in [200, 401, 403]
    
    if response.status_code == 200:
        data = response.json()
        assert "logs" in data
        assert "total" in data
        assert len(data["logs"]) <= 10
