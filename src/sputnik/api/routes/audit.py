"""Audit log API endpoints."""

from typing import Optional

from fastapi import APIRouter, Request, Query
from pydantic import BaseModel

from sputnik.api.db import get_audit_log_db
from sputnik.api.rbac import require_role

router = APIRouter()


# Response models
class AuditLogEntry(BaseModel):
    """Audit log entry model."""
    id: str
    user_id: Optional[str] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    details: Optional[dict] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: Optional[str] = None


class AuditLogsResponse(BaseModel):
    """Audit logs response."""
    logs: list[AuditLogEntry]
    total: int
    page: int
    page_size: int


@router.get("/audit/logs", response_model=AuditLogsResponse)
@require_role("admin")
async def get_audit_logs(
    request: Request,
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    action: Optional[str] = Query(None, description="Filter by action"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    resource_id: Optional[str] = Query(None, description="Filter by resource ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Page size"),
) -> AuditLogsResponse:
    """Get audit logs (admin only)."""
    audit_db = get_audit_log_db()
    
    result = audit_db.get_audit_logs(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        page=page,
        page_size=page_size,
    )
    
    return AuditLogsResponse(
        logs=[AuditLogEntry(**log) for log in result["logs"]],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
    )
