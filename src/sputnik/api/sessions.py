"""Session management utilities."""

import os
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from fastapi import Request

from sputnik.api.db import get_sessions_db


# Session configuration
SESSION_TIMEOUT_HOURS = int(os.getenv("SESSION_TIMEOUT_HOURS", "24"))
MAX_CONCURRENT_SESSIONS = int(os.getenv("MAX_CONCURRENT_SESSIONS", "5"))


def get_client_ip(request: Request) -> Optional[str]:
    """Get client IP address from request."""
    # Check for forwarded IP (from proxy/load balancer)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP in the chain
        return forwarded_for.split(",")[0].strip()
    
    # Check for real IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to direct client IP
    if request.client:
        return request.client.host
    
    return None


def get_user_agent(request: Request) -> Optional[str]:
    """Get user agent from request."""
    return request.headers.get("User-Agent")


def create_session(
    session_id: str,
    user_id: str,
    request: Request,
    expires_in_hours: Optional[int] = None,
) -> bool:
    """
    Create a new session.
    
    Args:
        session_id: Session ID (from Clerk token)
        user_id: User ID
        request: FastAPI request object
        expires_in_hours: Session expiration time in hours (default: SESSION_TIMEOUT_HOURS)
    
    Returns:
        True if session created successfully
    """
    if expires_in_hours is None:
        expires_in_hours = SESSION_TIMEOUT_HOURS
    
    sessions_db = get_sessions_db()
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    
    # Check concurrent session limit
    active_sessions = sessions_db.get_user_sessions(user_id, active_only=True)
    if len(active_sessions) >= MAX_CONCURRENT_SESSIONS:
        # Deactivate oldest session
        if active_sessions:
            oldest_session = active_sessions[-1]
            sessions_db.deactivate_session(oldest_session["session_id"])
    
    return sessions_db.create_session(
        session_id=session_id,
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
        expires_in_hours=expires_in_hours,
    )


def update_session_activity(session_id: str) -> bool:
    """
    Update session last activity timestamp.
    
    Args:
        session_id: Session ID
    
    Returns:
        True if updated successfully
    """
    sessions_db = get_sessions_db()
    return sessions_db.update_session_activity(session_id)


def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Get session by ID.
    
    Args:
        session_id: Session ID
    
    Returns:
        Session dict or None if not found/expired
    """
    sessions_db = get_sessions_db()
    return sessions_db.get_session(session_id)


def deactivate_session(session_id: str) -> bool:
    """
    Deactivate a session.
    
    Args:
        session_id: Session ID
    
    Returns:
        True if deactivated successfully
    """
    sessions_db = get_sessions_db()
    return sessions_db.deactivate_session(session_id)


def deactivate_user_sessions(user_id: str, keep_session_id: Optional[str] = None) -> int:
    """
    Deactivate all sessions for a user (except optionally one).
    
    Args:
        user_id: User ID
        keep_session_id: Optional session ID to keep active
    
    Returns:
        Number of sessions deactivated
    """
    sessions_db = get_sessions_db()
    return sessions_db.deactivate_user_sessions(user_id, keep_session_id)


def get_user_sessions(user_id: str, active_only: bool = True) -> List[Dict[str, Any]]:
    """
    Get all sessions for a user.
    
    Args:
        user_id: User ID
        active_only: Only return active sessions
    
    Returns:
        List of session dicts
    """
    sessions_db = get_sessions_db()
    return sessions_db.get_user_sessions(user_id, active_only=active_only)


def cleanup_expired_sessions() -> int:
    """
    Clean up expired sessions.
    
    Returns:
        Number of sessions cleaned up
    """
    sessions_db = get_sessions_db()
    return sessions_db.cleanup_expired_sessions()
