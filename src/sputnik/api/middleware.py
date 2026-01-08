"""Authentication middleware for FastAPI."""

from typing import Callable

from fastapi import Request, status
from fastapi.responses import JSONResponse

from sputnik.api.auth import verify_clerk_token


async def clerk_auth_middleware(request: Request, call_next: Callable) -> JSONResponse:
    """
    Middleware to verify Clerk authentication for protected routes.

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
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": str(e)},
            )

    return await call_next(request)

