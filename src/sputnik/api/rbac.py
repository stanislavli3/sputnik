"""Role-Based Access Control (RBAC) utilities."""

from functools import wraps
from typing import List, Optional, Callable, Any

from fastapi import Request, HTTPException, status

from sputnik.api.db import get_roles_db


def get_user_permissions(user_id: Optional[str]) -> List[str]:
    """
    Get all permissions for a user.
    
    Args:
        user_id: User ID (from Clerk token)
    
    Returns:
        List of permission strings (e.g., ["query:execute", "reviews:approve"])
        Returns ["*"] if user has admin role (all permissions)
    """
    if not user_id:
        return []
    
    roles_db = get_roles_db()
    return roles_db.get_user_permissions(user_id)


def get_user_roles(user_id: Optional[str]) -> List[str]:
    """
    Get all role IDs for a user.
    
    Args:
        user_id: User ID (from Clerk token)
    
    Returns:
        List of role IDs (e.g., ["admin", "finance_analyst"])
    """
    if not user_id:
        return []
    
    roles_db = get_roles_db()
    return roles_db.get_user_roles(user_id)


def has_permission(user_id: Optional[str], permission: str) -> bool:
    """
    Check if user has a specific permission.
    
    Args:
        user_id: User ID (from Clerk token)
        permission: Permission to check (e.g., "query:execute")
    
    Returns:
        True if user has permission, False otherwise
    """
    permissions = get_user_permissions(user_id)
    
    # Admin has all permissions
    if "*" in permissions:
        return True
    
    # Check exact match
    if permission in permissions:
        return True
    
    # Check wildcard permissions (e.g., "query:*" matches "query:execute")
    for perm in permissions:
        if perm.endswith(":*"):
            prefix = perm[:-2]
            if permission.startswith(prefix + ":"):
                return True
    
    return False


def has_role(user_id: Optional[str], role_id: str) -> bool:
    """
    Check if user has a specific role.
    
    Args:
        user_id: User ID (from Clerk token)
        role_id: Role ID to check (e.g., "admin")
    
    Returns:
        True if user has role, False otherwise
    """
    roles = get_user_roles(user_id)
    return role_id in roles


def require_permission(permission: str):
    """
    Decorator to require a specific permission for an endpoint.
    
    Usage:
        @router.post("/query")
        @require_permission("query:execute")
        async def execute_query(request: Request):
            ...
    
    Args:
        permission: Required permission (e.g., "query:execute")
    
    Raises:
        HTTPException: 403 if user doesn't have permission
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Find Request object in args or kwargs
            request: Optional[Request] = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                # Try kwargs
                request = kwargs.get("request")
            
            if not request:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Request object not found in endpoint",
                )
            
            # Get user from request state (set by auth middleware)
            user = getattr(request.state, "user", None)
            user_id = user.get("user_id") if user else None
            
            if not has_permission(user_id, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission required: {permission}",
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_role(role_id: str):
    """
    Decorator to require a specific role for an endpoint.
    
    Usage:
        @router.post("/admin/users")
        @require_role("admin")
        async def create_user(request: Request):
            ...
    
    Args:
        role_id: Required role ID (e.g., "admin")
    
    Raises:
        HTTPException: 403 if user doesn't have role
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Find Request object in args or kwargs
            request: Optional[Request] = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                request = kwargs.get("request")
            
            if not request:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Request object not found in endpoint",
                )
            
            # Get user from request state
            user = getattr(request.state, "user", None)
            user_id = user.get("user_id") if user else None
            
            if not has_role(user_id, role_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role required: {role_id}",
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_any_permission(*permissions: str):
    """
    Decorator to require any one of multiple permissions.
    
    Usage:
        @router.get("/data")
        @require_any_permission("query:execute", "query:view_history")
        async def get_data(request: Request):
            ...
    
    Args:
        *permissions: One or more permissions (user needs at least one)
    
    Raises:
        HTTPException: 403 if user doesn't have any of the permissions
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            request: Optional[Request] = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                request = kwargs.get("request")
            
            if not request:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Request object not found in endpoint",
                )
            
            user = getattr(request.state, "user", None)
            user_id = user.get("user_id") if user else None
            
            # Check if user has any of the required permissions
            has_any = any(has_permission(user_id, perm) for perm in permissions)
            
            if not has_any:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"One of these permissions required: {', '.join(permissions)}",
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator
