"""Tests for session management."""

import pytest
import os
from datetime import datetime, timedelta
from sputnik.api.db import SessionsDB
from sputnik.api.sessions import (
    create_session,
    get_session,
    update_session_activity,
    deactivate_session,
    deactivate_user_sessions,
    get_user_sessions,
)


@pytest.fixture
def sessions_db(temp_db, monkeypatch):
    """Create SessionsDB instance with test database."""
    from sputnik.api import db as db_module
    
    def get_test_sessions_db():
        return SessionsDB(db_path=temp_db)
    
    monkeypatch.setattr(db_module, "get_sessions_db", get_test_sessions_db)
    
    db = SessionsDB(db_path=temp_db)
    return db


@pytest.fixture
def mock_request():
    """Mock FastAPI request."""
    from unittest.mock import Mock
    
    request = Mock()
    request.headers = {
        "X-Forwarded-For": "192.168.1.1",
        "User-Agent": "Mozilla/5.0 Test Browser",
    }
    request.client = Mock()
    request.client.host = "127.0.0.1"
    return request


def test_create_session(sessions_db, mock_request, monkeypatch):
    """Test creating a new session."""
    from sputnik.api import sessions as sessions_module
    monkeypatch.setattr(sessions_module, "get_sessions_db", lambda: sessions_db)
    
    success = create_session(
        session_id="test_session_123",
        user_id="test_user_123",
        request=mock_request,
        expires_in_hours=24,
    )
    assert success is True
    
    # Verify session exists
    session = get_session("test_session_123")
    assert session is not None
    assert session["user_id"] == "test_user_123"
    assert session["is_active"] is True


def test_get_session_not_found(sessions_db, monkeypatch):
    """Test getting non-existent session."""
    from sputnik.api import sessions as sessions_module
    monkeypatch.setattr(sessions_module, "get_sessions_db", lambda: sessions_db)
    
    session = get_session("nonexistent_session")
    assert session is None


def test_update_session_activity(sessions_db, mock_request, monkeypatch):
    """Test updating session activity."""
    from sputnik.api import sessions as sessions_module
    monkeypatch.setattr(sessions_module, "get_sessions_db", lambda: sessions_db)
    
    # Create session
    create_session("test_session_123", "test_user_123", mock_request)
    
    # Get initial activity time
    session1 = get_session("test_session_123")
    initial_activity = session1["last_activity"]
    
    # Wait a bit and update
    import time
    time.sleep(0.1)
    update_session_activity("test_session_123")
    
    # Verify activity was updated
    session2 = get_session("test_session_123")
    assert session2["last_activity"] != initial_activity


def test_deactivate_session(sessions_db, mock_request, monkeypatch):
    """Test deactivating a session."""
    from sputnik.api import sessions as sessions_module
    monkeypatch.setattr(sessions_module, "get_sessions_db", lambda: sessions_db)
    
    # Create session
    create_session("test_session_123", "test_user_123", mock_request)
    
    # Deactivate it
    success = deactivate_session("test_session_123")
    assert success is True
    
    # Verify session is inactive
    session = get_session("test_session_123")
    assert session is None  # get_session only returns active sessions


def test_deactivate_user_sessions(sessions_db, mock_request, monkeypatch):
    """Test deactivating all sessions for a user."""
    from sputnik.api import sessions as sessions_module
    monkeypatch.setattr(sessions_module, "get_sessions_db", lambda: sessions_db)
    
    # Create multiple sessions
    create_session("session_1", "test_user_123", mock_request)
    create_session("session_2", "test_user_123", mock_request)
    create_session("session_3", "other_user", mock_request)
    
    # Deactivate all sessions for test_user_123
    count = deactivate_user_sessions("test_user_123", keep_session_id="session_1")
    assert count == 1  # Should deactivate session_2
    
    # Verify session_1 is still active
    assert get_session("session_1") is not None
    
    # Verify session_2 is inactive
    assert get_session("session_2") is None
    
    # Verify other_user's session is still active
    assert get_session("session_3") is not None


def test_get_user_sessions(sessions_db, mock_request, monkeypatch):
    """Test getting all sessions for a user."""
    from sputnik.api import sessions as sessions_module
    monkeypatch.setattr(sessions_module, "get_sessions_db", lambda: sessions_db)
    
    # Create multiple sessions
    create_session("session_1", "test_user_123", mock_request)
    create_session("session_2", "test_user_123", mock_request)
    create_session("session_3", "other_user", mock_request)
    
    # Get sessions for test_user_123
    sessions = get_user_sessions("test_user_123", active_only=True)
    assert len(sessions) == 2
    assert all(s["user_id"] == "test_user_123" for s in sessions)


def test_session_expiration(sessions_db, mock_request, monkeypatch):
    """Test that expired sessions are not returned."""
    from sputnik.api import sessions as sessions_module
    monkeypatch.setattr(sessions_module, "get_sessions_db", lambda: sessions_db)
    
    # Create session with short expiration
    sessions_db.create_session(
        session_id="expired_session",
        user_id="test_user_123",
        ip_address="127.0.0.1",
        user_agent="Test",
        expires_in_hours=-1,  # Already expired
    )
    
    # Session should not be returned
    session = get_session("expired_session")
    assert session is None


def test_concurrent_session_limit(sessions_db, mock_request, monkeypatch):
    """Test concurrent session limit."""
    from sputnik.api import sessions as sessions_module
    monkeypatch.setattr(sessions_module, "get_sessions_db", lambda: sessions_db)
    import os
    os.environ["MAX_CONCURRENT_SESSIONS"] = "2"
    
    # Create 3 sessions (exceeds limit)
    create_session("session_1", "test_user_123", mock_request)
    create_session("session_2", "test_user_123", mock_request)
    create_session("session_3", "test_user_123", mock_request)
    
    # Should have only 2 active sessions (oldest deactivated)
    sessions = get_user_sessions("test_user_123", active_only=True)
    assert len(sessions) <= 2
