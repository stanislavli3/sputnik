"""Session management API endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Request, HTTPException, status
from pydantic import BaseModel

from sputnik.api.db import get_sessions_db
from sputnik.api.sessions import (
    get_user_sessions,
    deactivate_session,
    deactivate_user_sessions,
    get_session,
)
from sputnik.api.rbac import require_permission, require_role
from sputnik.api.audit import log_action

router = APIRouter()


# Response models
class SessionResponse(BaseModel):
    """Session response model."""
    session_id: str
    user_id: str
    created_at: Optional[str] = None
    last_activity: Optional[str] = None
    expires_at: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    is_active: bool


class SessionsListResponse(BaseModel):
    """List of sessions response."""
    sessions: List[SessionResponse]


@router.get("/sessions/me", response_model=SessionsListResponse)
async def get_my_sessions(request: Request) -> SessionsListResponse:
    """Get current user's active sessions."""
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    user_id = user.get("user_id")
    sessions = get_user_sessions(user_id, active_only=True)
    
    return SessionsListResponse(
        sessions=[SessionResponse(**session) for session in sessions]
    )


@router.get("/sessions/{session_id}", response_model=SessionResponse)
@require_permission("sessions:view")
async def get_session_endpoint(
    request: Request,
    session_id: str,
) -> SessionResponse:
    """Get a specific session by ID."""
    session = get_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    
    # Check if user has permission to view this session
    user = getattr(request.state, "user", None)
    user_id = user.get("user_id") if user else None
    
    # Users can only view their own sessions unless they're admin
    if session["user_id"] != user_id:
        from sputnik.api.rbac import has_role
        if not has_role(user_id, "admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot view other users' sessions",
            )
    
    return SessionResponse(**session)


@router.get("/users/{user_id}/sessions", response_model=SessionsListResponse)
@require_role("admin")
async def get_user_sessions_endpoint(
    request: Request,
    user_id: str,
    active_only: bool = True,
) -> SessionsListResponse:
    """Get all sessions for a user (admin only)."""
    sessions = get_user_sessions(user_id, active_only=active_only)
    
    return SessionsListResponse(
        sessions=[SessionResponse(**session) for session in sessions]
    )


@router.post("/sessions/{session_id}/deactivate")
async def deactivate_session_endpoint(
    request: Request,
    session_id: str,
) -> dict:
    """Deactivate a session (users can deactivate their own sessions)."""
    session = get_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    
    # Check if user has permission to deactivate this session
    user = getattr(request.state, "user", None)
    user_id = user.get("user_id") if user else None
    
    # Users can only deactivate their own sessions unless they're admin
    if session["user_id"] != user_id:
        from sputnik.api.rbac import has_role
        if not has_role(user_id, "admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot deactivate other users' sessions",
            )
    
    success = deactivate_session(session_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate session",
        )
    
    # Audit log
    log_action(
        user_id=user_id,
        action="session_deactivated",
        resource_type="session",
        resource_id=session_id,
        details={"target_user_id": session["user_id"]},
        request=request,
    )
    
    return {
        "message": "Session deactivated successfully",
        "session_id": session_id,
    }


@router.post("/sessions/me/deactivate-all")
async def deactivate_all_my_sessions(
    request: Request,
    keep_current: bool = True,
) -> dict:
    """Deactivate all sessions for current user (except optionally current one)."""
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    user_id = user.get("user_id")
    session_id = user.get("session_id") if keep_current else None
    
    count = deactivate_user_sessions(user_id, keep_session_id=session_id)
    
    # Audit log
    log_action(
        user_id=user_id,
        action="sessions_deactivated",
        resource_type="session",
        details={"count": count, "keep_current": keep_current},
        request=request,
    )
    
    return {
        "message": f"Deactivated {count} session(s)",
        "count": count,
    }
