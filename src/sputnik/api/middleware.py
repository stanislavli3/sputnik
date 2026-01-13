"""Authentication middleware for FastAPI."""

from typing import Callable

from fastapi import Request, status
from fastapi.responses import JSONResponse

from sputnik.api.auth import verify_clerk_token
from sputnik.api.sessions import create_session, update_session_activity, get_session
from sputnik.api.audit import log_request


async def clerk_auth_middleware(request: Request, call_next: Callable) -> JSONResponse:
    """
    Middleware to verify Clerk authentication for protected routes.
    Also handles session management and audit logging.

    Args:
        request: FastAPI request
        call_next: Next middleware/route handler

    Returns:
        Response from next handler or error response
    """
    # Skip auth for public endpoints
    public_paths = ["/", "/health", "/docs", "/openapi.json", "/redoc"]
    if request.url.path in public_paths:
        return await call_next(request)

    # Skip auth for OPTIONS requests (CORS preflight)
    if request.method == "OPTIONS":
        return await call_next(request)

    # Verify authentication for API routes
    if request.url.path.startswith("/api/"):
        try:
            user = await verify_clerk_token(request)
            # Attach user to request state
            request.state.user = user
            
            # Session management
            user_id = user.get("user_id")
            session_id = user.get("session_id")
            
            if user_id and session_id:
                # Check if session exists and is valid
                session = get_session(session_id)
                
                if not session:
                    # Create new session
                    create_session(session_id, user_id, request)
                else:
                    # Update session activity
                    update_session_activity(session_id)
            
            # Audit logging (async, non-blocking)
            try:
                log_request(request, user)
            except Exception:
                pass  # Don't fail request if audit logging fails
            
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": str(e)},
            )

    return await call_next(request)

