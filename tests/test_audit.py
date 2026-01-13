"""Tests for audit logging."""

import pytest
from sputnik.api.db import AuditLogDB


@pytest.fixture
def audit_db(temp_db):
    """Create AuditLogDB instance with test database."""
    db = AuditLogDB(db_path=temp_db)
    return db


def test_log_action(audit_db):
    """Test logging an audit action."""
    from sputnik.api.audit import log_action
    
    log_id = audit_db.log_action(
        user_id="test_user_123",
        action="query_executed",
        resource_type="query",
        resource_id="query_123",
        details={"question": "Test question"},
        ip_address="127.0.0.1",
        user_agent="Test Browser",
    )
    
    assert log_id is not None
    assert len(log_id) > 0


def test_get_audit_logs(audit_db):
    """Test retrieving audit logs."""
    # Create some audit logs
    audit_db.log_action("user_1", "query_executed", "query", "q1")
    audit_db.log_action("user_2", "review_approved", "review", "r1")
    audit_db.log_action("user_1", "query_executed", "query", "q2")
    
    # Get all logs
    result = audit_db.get_audit_logs()
    assert result["total"] == 3
    assert len(result["logs"]) == 3


def test_get_audit_logs_filter_by_user(audit_db):
    """Test filtering audit logs by user."""
    audit_db.log_action("user_1", "query_executed", "query", "q1")
    audit_db.log_action("user_2", "review_approved", "review", "r1")
    audit_db.log_action("user_1", "query_executed", "query", "q2")
    
    # Filter by user_1
    result = audit_db.get_audit_logs(user_id="user_1")
    assert result["total"] == 2
    assert all(log["user_id"] == "user_1" for log in result["logs"])


def test_get_audit_logs_filter_by_action(audit_db):
    """Test filtering audit logs by action."""
    audit_db.log_action("user_1", "query_executed", "query", "q1")
    audit_db.log_action("user_2", "review_approved", "review", "r1")
    audit_db.log_action("user_1", "query_executed", "query", "q2")
    
    # Filter by action
    result = audit_db.get_audit_logs(action="query_executed")
    assert result["total"] == 2
    assert all(log["action"] == "query_executed" for log in result["logs"])


def test_get_audit_logs_filter_by_resource(audit_db):
    """Test filtering audit logs by resource."""
    audit_db.log_action("user_1", "query_executed", "query", "q1")
    audit_db.log_action("user_2", "review_approved", "review", "r1")
    audit_db.log_action("user_1", "query_executed", "query", "q2")
    
    # Filter by resource type
    result = audit_db.get_audit_logs(resource_type="query")
    assert result["total"] == 2
    assert all(log["resource_type"] == "query" for log in result["logs"])


def test_get_audit_logs_pagination(audit_db):
    """Test pagination of audit logs."""
    # Create 10 audit logs
    for i in range(10):
        audit_db.log_action(f"user_{i}", "query_executed", "query", f"q{i}")
    
    # Get first page
    result1 = audit_db.get_audit_logs(page=1, page_size=5)
    assert result1["total"] == 10
    assert len(result1["logs"]) == 5
    
    # Get second page
    result2 = audit_db.get_audit_logs(page=2, page_size=5)
    assert result2["total"] == 10
    assert len(result2["logs"]) == 5
    
    # Verify different logs
    assert result1["logs"][0]["id"] != result2["logs"][0]["id"]


def test_log_action_with_details(audit_db):
    """Test logging action with complex details."""
    details = {
        "question": "What is total revenue?",
        "sql_queries": ["SELECT SUM(amount) FROM orders"],
        "confidence": 0.85,
    }
    
    log_id = audit_db.log_action(
        user_id="test_user_123",
        action="query_executed",
        details=details,
    )
    
    # Retrieve and verify details
    result = audit_db.get_audit_logs()
    log = next((l for l in result["logs"] if l["id"] == log_id), None)
    assert log is not None
    assert log["details"] == details
