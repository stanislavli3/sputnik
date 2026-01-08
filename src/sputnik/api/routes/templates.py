"""Query template endpoints."""

from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from sputnik.api.db import get_templates_db

router = APIRouter()


class QueryTemplate(BaseModel):
    """Query template model."""

    id: str
    name: str
    category: Optional[str] = None
    question: str
    sql_template: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None
    created_by: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class CreateTemplateRequest(BaseModel):
    """Create template request model."""

    name: str
    question: str
    sql_template: Optional[str] = None
    category: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None


class UpdateTemplateRequest(BaseModel):
    """Update template request model."""

    name: Optional[str] = None
    question: Optional[str] = None
    sql_template: Optional[str] = None
    category: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None


@router.get("/queries/templates", response_model=list[QueryTemplate])
async def list_templates(
    category: Optional[str] = None,
    http_request: Request = None,
) -> list[QueryTemplate]:
    """
    List query templates.

    Args:
        category: Filter by category
        http_request: HTTP request (for user info)

    Returns:
        List of templates
    """
    try:
        user_id = None
        if http_request:
            user = getattr(http_request.state, "user", None)
            if user:
                user_id = user.get("id")
        
        templates_db = get_templates_db()
        templates = templates_db.get_templates(category=category, created_by=user_id)
        
        return [QueryTemplate(**t) for t in templates]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/queries/templates/{template_id}", response_model=QueryTemplate)
async def get_template(
    template_id: str,
    http_request: Request = None,
) -> QueryTemplate:
    """
    Get a specific template by ID.

    Args:
        template_id: Template ID
        http_request: HTTP request (for user info)

    Returns:
        Template
    """
    try:
        templates_db = get_templates_db()
        template = templates_db.get_template(template_id)
        
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        return QueryTemplate(**template)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/queries/templates", response_model=QueryTemplate)
async def create_template(
    request: CreateTemplateRequest,
    http_request: Request = None,
) -> QueryTemplate:
    """
    Create a new query template.

    Args:
        request: Template creation request
        http_request: HTTP request (for user info)

    Returns:
        Created template
    """
    try:
        user_id = None
        if http_request:
            user = getattr(http_request.state, "user", None)
            if user:
                user_id = user.get("id")
        
        templates_db = get_templates_db()
        template_id = templates_db.create_template(
            name=request.name,
            question=request.question,
            sql_template=request.sql_template,
            category=request.category,
            variables=request.variables,
            created_by=user_id,
        )
        
        template = templates_db.get_template(template_id)
        return QueryTemplate(**template)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/queries/templates/{template_id}", response_model=QueryTemplate)
async def update_template(
    template_id: str,
    request: UpdateTemplateRequest,
    http_request: Request = None,
) -> QueryTemplate:
    """
    Update a template.

    Args:
        template_id: Template ID
        request: Template update request
        http_request: HTTP request (for user info)

    Returns:
        Updated template
    """
    try:
        templates_db = get_templates_db()
        success = templates_db.update_template(
            template_id=template_id,
            name=request.name,
            question=request.question,
            sql_template=request.sql_template,
            category=request.category,
            variables=request.variables,
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Template not found")
        
        template = templates_db.get_template(template_id)
        return QueryTemplate(**template)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/queries/templates/{template_id}")
async def delete_template(
    template_id: str,
    http_request: Request = None,
) -> dict:
    """
    Delete a template.

    Args:
        template_id: Template ID
        http_request: HTTP request (for user info)

    Returns:
        Success message
    """
    try:
        templates_db = get_templates_db()
        success = templates_db.delete_template(template_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Template not found")
        
        return {"message": "Template deleted", "template_id": template_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
