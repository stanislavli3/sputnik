"""User and role management API endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Request, HTTPException, status
from pydantic import BaseModel

from sputnik.api.db import get_roles_db
from sputnik.api.rbac import require_role, require_permission, get_user_roles, get_user_permissions
from sputnik.api.audit import log_action

router = APIRouter()


# Request/Response models
class RoleResponse(BaseModel):
    """Role response model."""
    id: str
    name: str
    description: Optional[str] = None
    permissions: List[str]
    created_at: Optional[str] = None


class UserRoleResponse(BaseModel):
    """User role response model."""
    user_id: str
    roles: List[str]
    permissions: List[str]


class AssignRoleRequest(BaseModel):
    """Request to assign a role."""
    user_id: str
    role_id: str


class RevokeRoleRequest(BaseModel):
    """Request to revoke a role."""
    user_id: str
    role_id: str


class RolesListResponse(BaseModel):
    """List of roles response."""
    roles: List[RoleResponse]


@router.get("/users/roles", response_model=RolesListResponse)
@require_permission("roles:view")
async def list_roles(request: Request) -> RolesListResponse:
    """List all available roles."""
    roles_db = get_roles_db()
    roles = roles_db.get_all_roles()
    
    return RolesListResponse(
        roles=[RoleResponse(**role) for role in roles]
    )


@router.get("/users/{user_id}/roles", response_model=UserRoleResponse)
@require_permission("roles:view")
async def get_user_roles_endpoint(
    request: Request,
    user_id: str,
) -> UserRoleResponse:
    """Get roles and permissions for a user."""
    roles = get_user_roles(user_id)
    permissions = get_user_permissions(user_id)
    
    return UserRoleResponse(
        user_id=user_id,
        roles=roles,
        permissions=permissions,
    )


@router.get("/users/me/roles", response_model=UserRoleResponse)
async def get_my_roles(request: Request) -> UserRoleResponse:
    """Get current user's roles and permissions."""
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    user_id = user.get("user_id")
    roles = get_user_roles(user_id)
    permissions = get_user_permissions(user_id)
    
    return UserRoleResponse(
        user_id=user_id,
        roles=roles,
        permissions=permissions,
    )


@router.post("/users/roles/assign")
@require_role("admin")
async def assign_role(
    request: Request,
    body: AssignRoleRequest,
) -> dict:
    """Assign a role to a user (admin only)."""
    roles_db = get_roles_db()
    
    # Verify role exists
    role = roles_db.get_role(body.role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role not found: {body.role_id}",
        )
    
    # Assign role
    success = roles_db.assign_role(
        user_id=body.user_id,
        role_id=body.role_id,
        assigned_by=getattr(request.state, "user", {}).get("user_id"),
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign role",
        )
    
    # Audit log
    user = getattr(request.state, "user", None)
    log_action(
        user_id=user.get("user_id") if user else None,
        action="role_assigned",
        resource_type="role",
        resource_id=body.role_id,
        details={"user_id": body.user_id, "role_id": body.role_id},
        request=request,
    )
    
    return {
        "message": "Role assigned successfully",
        "user_id": body.user_id,
        "role_id": body.role_id,
    }


@router.post("/users/roles/revoke")
@require_role("admin")
async def revoke_role(
    request: Request,
    body: RevokeRoleRequest,
) -> dict:
    """Revoke a role from a user (admin only)."""
    roles_db = get_roles_db()
    
    success = roles_db.revoke_role(
        user_id=body.user_id,
        role_id=body.role_id,
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke role",
        )
    
    # Audit log
    user = getattr(request.state, "user", None)
    log_action(
        user_id=user.get("user_id") if user else None,
        action="role_revoked",
        resource_type="role",
        resource_id=body.role_id,
        details={"user_id": body.user_id, "role_id": body.role_id},
        request=request,
    )
    
    return {
        "message": "Role revoked successfully",
        "user_id": body.user_id,
        "role_id": body.role_id,
    }
