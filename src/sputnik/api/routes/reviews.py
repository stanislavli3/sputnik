"""Review endpoints."""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from sputnik.api.db import get_reviews_db, get_history_db

router = APIRouter()


class ReviewItem(BaseModel):
    """Review item model."""

    id: str
    query_id: str
    expert_id: Optional[str] = None
    status: str
    correction_reason: Optional[str] = None
    expert_notes: Optional[str] = None
    corrected_answer: Optional[str] = None
    priority: str
    created_at: Optional[str] = None
    reviewed_at: Optional[str] = None
    submitted_by: str
    question: str
    answer: Optional[str] = None
    confidence: float
    risk: str
    wait_time: Optional[str] = None
    sql_queries: List[str] = []
    execution_results: Optional[dict] = None


class ReviewsResponse(BaseModel):
    """Reviews response model."""

    reviews: List[ReviewItem]
    total: int


class ReviewActionRequest(BaseModel):
    """Review action request model."""

    correction_reason: Optional[str] = None
    expert_notes: Optional[str] = None
    corrected_answer: Optional[str] = None


@router.get("/reviews", response_model=ReviewsResponse)
async def list_reviews(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    http_request: Request = None,
) -> ReviewsResponse:
    """
    List reviews with optional filtering.

    Args:
        status: Filter by status (pending, approved, rejected, abstained)
        priority: Filter by priority (high, medium, low)
        http_request: HTTP request (for user info)

    Returns:
        List of reviews
    """
    try:
        reviews_db = get_reviews_db()
        
        # Get expert_id from request if available
        expert_id = None
        if http_request:
            user = getattr(http_request.state, "user", None)
            if user:
                expert_id = user.get("id")
        
        reviews = reviews_db.get_reviews(
            status=status,
            priority=priority,
            expert_id=expert_id if status == "assigned" else None,  # Only filter by expert if status is "assigned"
        )
        
        # Convert to response model
        review_items = [ReviewItem(**r) for r in reviews]
        
        return ReviewsResponse(reviews=review_items, total=len(review_items))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reviews/{review_id}", response_model=ReviewItem)
async def get_review(
    review_id: str,
    http_request: Request = None,
) -> ReviewItem:
    """
    Get a specific review by ID.

    Args:
        review_id: Review ID
        http_request: HTTP request (for user info)

    Returns:
        Review item
    """
    try:
        reviews_db = get_reviews_db()
        review = reviews_db.get_review(review_id)
        
        if not review:
            raise HTTPException(status_code=404, detail="Review not found")
        
        return ReviewItem(**review)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reviews/{review_id}/approve")
async def approve_review(
    review_id: str,
    request: ReviewActionRequest,
    http_request: Request = None,
) -> dict:
    """
    Approve a review.

    Args:
        review_id: Review ID
        request: Review action request
        http_request: HTTP request (for user info)

    Returns:
        Success message
    """
    try:
        expert_id = None
        if http_request:
            user = getattr(http_request.state, "user", None)
            if user:
                expert_id = user.get("id")
        
        reviews_db = get_reviews_db()
        success = reviews_db.update_review(
            review_id=review_id,
            status="approved",
            expert_id=expert_id,
            expert_notes=request.expert_notes,
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Review not found")
        
        return {"message": "Review approved", "review_id": review_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reviews/{review_id}/reject")
async def reject_review(
    review_id: str,
    request: ReviewActionRequest,
    http_request: Request = None,
) -> dict:
    """
    Reject a review.

    Args:
        review_id: Review ID
        request: Review action request
        http_request: HTTP request (for user info)

    Returns:
        Success message
    """
    try:
        expert_id = None
        if http_request:
            user = getattr(http_request.state, "user", None)
            if user:
                expert_id = user.get("id")
        
        reviews_db = get_reviews_db()
        success = reviews_db.update_review(
            review_id=review_id,
            status="rejected",
            expert_id=expert_id,
            correction_reason=request.correction_reason,
            expert_notes=request.expert_notes,
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Review not found")
        
        return {"message": "Review rejected", "review_id": review_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reviews/{review_id}/edit")
async def edit_and_approve_review(
    review_id: str,
    request: ReviewActionRequest,
    http_request: Request = None,
) -> dict:
    """
    Edit and approve a review.

    Args:
        review_id: Review ID
        request: Review action request (must include corrected_answer)
        http_request: HTTP request (for user info)

    Returns:
        Success message
    """
    try:
        if not request.corrected_answer:
            raise HTTPException(status_code=400, detail="corrected_answer is required")
        
        expert_id = None
        if http_request:
            user = getattr(http_request.state, "user", None)
            if user:
                expert_id = user.get("id")
        
        reviews_db = get_reviews_db()
        success = reviews_db.update_review(
            review_id=review_id,
            status="approved",
            expert_id=expert_id,
            correction_reason=request.correction_reason or "expert-edit",
            expert_notes=request.expert_notes,
            corrected_answer=request.corrected_answer,
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Review not found")
        
        return {"message": "Review edited and approved", "review_id": review_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reviews/{review_id}/abstain")
async def abstain_review(
    review_id: str,
    request: ReviewActionRequest,
    http_request: Request = None,
) -> dict:
    """
    Abstain from reviewing.

    Args:
        review_id: Review ID
        request: Review action request
        http_request: HTTP request (for user info)

    Returns:
        Success message
    """
    try:
        expert_id = None
        if http_request:
            user = getattr(http_request.state, "user", None)
            if user:
                expert_id = user.get("id")
        
        reviews_db = get_reviews_db()
        success = reviews_db.update_review(
            review_id=review_id,
            status="abstained",
            expert_id=expert_id,
            expert_notes=request.expert_notes,
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Review not found")
        
        return {"message": "Review abstained", "review_id": review_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
