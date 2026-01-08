"""Query history endpoints."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from sputnik.api.db import get_history_db

router = APIRouter()


class QueryHistoryItem(BaseModel):
    """Query history item model."""

    id: str
    user_id: Optional[str] = None
    question: str
    sql_queries: list[str]
    answer: str
    confidence: float
    execution_results: Optional[dict] = None
    execution_time_ms: Optional[int] = None
    model_id: Optional[str] = None
    created_at: str


class QueryHistoryResponse(BaseModel):
    """Query history response model."""

    queries: list[QueryHistoryItem]
    total: int
    page: int
    page_size: int


@router.get("/queries/history", response_model=QueryHistoryResponse)
async def get_query_history(
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    http_request: Request = None,
) -> QueryHistoryResponse:
    """
    Get query history with pagination.

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
        search: Search term to filter by question
        http_request: HTTP request (for user info)

    Returns:
        Paginated query history
    """
    try:
        # Access authenticated user if available
        user = getattr(http_request.state, "user", None) if http_request else None
        user_id = user.get("id") if user else None
        
        history_db = get_history_db()
        result = history_db.get_query_history(
            user_id=user_id,
            page=page,
            page_size=page_size,
            search=search,
        )
        
        # Convert to response model
        queries = [
            QueryHistoryItem(**q) for q in result["queries"]
        ]
        
        return QueryHistoryResponse(
            queries=queries,
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/queries/{query_id}", response_model=QueryHistoryItem)
async def get_query(
    query_id: str,
    http_request: Request = None,
) -> QueryHistoryItem:
    """
    Get a specific query by ID.

    Args:
        query_id: Query ID
        http_request: HTTP request (for user info)

    Returns:
        Query history item
    """
    try:
        history_db = get_history_db()
        query = history_db.get_query(query_id)
        
        if not query:
            raise HTTPException(status_code=404, detail="Query not found")
        
        # Check user access (optional - can be enhanced with proper auth)
        user = getattr(http_request.state, "user", None) if http_request else None
        user_id = user.get("id") if user else None
        
        # For now, allow access to all queries (can add permission check later)
        # if query["user_id"] and query["user_id"] != user_id:
        #     raise HTTPException(status_code=403, detail="Access denied")
        
        return QueryHistoryItem(**query)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
