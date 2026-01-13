"""Audit logging utilities."""

import json
from typing import Optional, Dict, Any

from fastapi import Request

from sputnik.api.db import get_audit_log_db
from sputnik.api.sessions import get_client_ip, get_user_agent


# Actions to audit (critical operations)
AUDIT_ACTIONS = {
    "query:execute": "query_executed",
    "query:delete": "query_deleted",
    "review:create": "review_created",
    "review:approve": "review_approved",
    "review:reject": "review_rejected",
    "review:edit": "review_edited",
    "role:assign": "role_assigned",
    "role:revoke": "role_revoked",
    "user:create": "user_created",
    "user:delete": "user_deleted",
    "session:deactivate": "session_deactivated",
    "template:create": "template_created",
    "template:delete": "template_deleted",
    "export:download": "export_downloaded",
}


def log_action(
    user_id: Optional[str],
    action: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    request: Optional[Request] = None,
) -> str:
    """
    Log an audit action.
    
    Args:
        user_id: User ID performing the action
        action: Action name (e.g., "query_executed")
        resource_type: Type of resource (e.g., "query", "review")
        resource_id: ID of the resource
        details: Additional details to log
        request: FastAPI request object (for IP/user agent)
    
    Returns:
        Audit log ID
    """
    audit_db = get_audit_log_db()
    
    ip_address = None
    user_agent = None
    if request:
        ip_address = get_client_ip(request)
        user_agent = get_user_agent(request)
    
    return audit_db.log_action(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent,
    )


def log_request(request: Request, user: Optional[Dict[str, Any]]) -> None:
    """
    Log API request for audit purposes.
    Only logs critical actions, not all requests.
    
    Args:
        request: FastAPI request object
        user: User dict from request.state.user
    """
    # Only log POST, PUT, DELETE requests (state-changing operations)
    if request.method not in ["POST", "PUT", "DELETE", "PATCH"]:
        return
    
    # Extract action from path
    path = request.url.path
    method = request.method.lower()
    
    # Map common patterns to actions
    action = None
    resource_type = None
    resource_id = None
    
    # Query execution
    if path.endswith("/query") and method == "post":
        action = "query_executed"
        resource_type = "query"
    
    # Review actions
    elif "/reviews/" in path:
        resource_type = "review"
        if "/approve" in path:
            action = "review_approved"
            resource_id = path.split("/")[-2] if "/approve" in path else None
        elif "/reject" in path:
            action = "review_rejected"
            resource_id = path.split("/")[-2] if "/reject" in path else None
        elif "/edit" in path:
            action = "review_edited"
            resource_id = path.split("/")[-2] if "/edit" in path else None
        elif method == "post":
            action = "review_created"
    
    # Role management
    elif "/roles/" in path and "/assign" in path:
        action = "role_assigned"
        resource_type = "role"
    elif "/roles/" in path and "/revoke" in path:
        action = "role_revoked"
        resource_type = "role"
    
    # Template actions
    elif "/templates" in path:
        resource_type = "template"
        if method == "post":
            action = "template_created"
        elif method == "delete":
            action = "template_deleted"
            resource_id = path.split("/")[-1]
    
    # Export
    elif "/export" in path:
        action = "export_downloaded"
        resource_type = "query"
        resource_id = path.split("/")[-2] if "/export" in path else None
    
    # Session management
    elif "/sessions/" in path and "/deactivate" in path:
        action = "session_deactivated"
        resource_type = "session"
        resource_id = path.split("/")[-2] if "/deactivate" in path else None
    
    # Only log if we identified an action
    if action:
        user_id = user.get("user_id") if user else None
        
        # Try to extract details from request body (non-blocking)
        details = None
        try:
            if hasattr(request, "_body"):
                body = request._body
                if body:
                    details = json.loads(body.decode()) if isinstance(body, bytes) else body
        except:
            pass
        
        log_action(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            request=request,
        )


def audit_logged(action: str, resource_type: Optional[str] = None):
    """
    Decorator to explicitly log an audit action.
    
    Usage:
        @router.post("/query")
        @audit_logged("query_executed", resource_type="query")
        async def execute_query(request: Request, ...):
            ...
    
    Args:
        action: Action name to log
        resource_type: Type of resource
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Find Request object
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                request = kwargs.get("request")
            
            # Get user
            user = None
            if request:
                user = getattr(request.state, "user", None)
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Extract resource_id from result if possible
            resource_id = None
            if isinstance(result, dict):
                resource_id = result.get("id") or result.get("query_id") or result.get("review_id")
            
            # Log action
            if request:
                user_id = user.get("user_id") if user else None
                log_action(
                    user_id=user_id,
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    request=request,
                )
            
            return result
        
        return wrapper
    return decorator
