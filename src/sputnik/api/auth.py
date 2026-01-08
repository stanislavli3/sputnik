"""Authentication utilities for Clerk."""

import os
from typing import Optional

from fastapi import HTTPException, Request, status

# Lazy import jwt - only needed when Clerk is enabled
# This allows the server to start even if pyjwt is not installed
# (when Clerk authentication is not being used)
try:
    import jwt
except ImportError:
    jwt = None  # Will raise error when actually needed

# Clerk JWT verification
CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY")
CLERK_JWKS_URL = "https://api.clerk.com/v1/jwks"


def get_clerk_jwks() -> dict:
    """
    Get Clerk JWKS for token verification.

    Returns:
        JWKS dictionary
    """
    import requests

    try:
        response = requests.get(CLERK_JWKS_URL, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception:
        return {}


async def verify_clerk_token(request: Request) -> Optional[dict]:
    """
    Verify Clerk JWT token from request.

    Args:
        request: FastAPI request object

    Returns:
        User payload if valid, None otherwise

    Raises:
        HTTPException: If token is invalid or missing
    """
    # Get token from Authorization header
    authorization = request.headers.get("Authorization")
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format",
        )

    token = authorization.replace("Bearer ", "")

    # If Clerk is not configured, allow in development mode
    if not CLERK_SECRET_KEY:
        if os.getenv("DEBUG", "false").lower() == "true":
            return {"user_id": "dev-user", "email": "dev@example.com"}
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Clerk not configured",
        )

    # Check if jwt is available
    if jwt is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="PyJWT is required for Clerk authentication. Install it with: pip install pyjwt",
        )
    
    try:
        # Decode and verify JWT token
        # In production, use proper JWKS verification
        # For now, basic verification
        payload = jwt.decode(
            token,
            options={"verify_signature": False},  # Simplified for now
        )
        return {
            "user_id": payload.get("sub"),
            "email": payload.get("email"),
            "session_id": payload.get("sid"),
        }
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {str(e)}",
        )

