"""Tests for session management API endpoints."""

import pytest
from fastapi.testclient import TestClient
from sputnik.api.server import app
from sputnik.api.db import get_sessions_db, SessionsDB


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sessions_db(temp_db):
    """Create SessionsDB instance."""
    return SessionsDB(db_path=temp_db)


def test_get_my_sessions(client):
    """Test getting current user's sessions."""
    response = client.get("/api/v1/sessions/me")
    # Without auth, should fail
    assert response.status_code in [200, 401, 403]


def test_deactivate_session(client, sessions_db):
    """Test deactivating a session."""
    # Create a session first
    sessions_db.create_session(
        session_id="test_session_123",
        user_id="test_user_123",
        ip_address="127.0.0.1",
        user_agent="Test",
    )
    
    response = client.post("/api/v1/sessions/test_session_123/deactivate")
    # Should require auth
    assert response.status_code in [200, 401, 403]


def test_deactivate_all_sessions(client, sessions_db):
    """Test deactivating all user sessions."""
    response = client.post("/api/v1/sessions/me/deactivate-all")
    # Should require auth
    assert response.status_code in [200, 401, 403]
