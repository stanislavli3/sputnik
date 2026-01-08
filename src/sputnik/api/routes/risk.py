"""Risk assessment endpoints."""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from sputnik.api.db import get_history_db
from sputnik.api.risk import calculate_risk_assessment

router = APIRouter()


class ConfidenceFactor(BaseModel):
    """Confidence factor model."""

    query_interpretation: float
    data_completeness: float
    schema_match: float
    historical_accuracy: float


class RiskFactor(BaseModel):
    """Risk factor model."""

    severity: str
    title: str
    description: str


class RiskAssessmentResponse(BaseModel):
    """Risk assessment response model."""

    overall_risk: str
    confidence_factors: ConfidenceFactor
    risk_factors: list[RiskFactor]
    allowed_actions: list[str]
    recommended_action: str


@router.get("/query/{query_id}/risk", response_model=RiskAssessmentResponse)
async def get_risk_assessment(
    query_id: str,
    http_request: Request = None,
) -> RiskAssessmentResponse:
    """
    Get risk assessment for a specific query.

    Args:
        query_id: Query ID
        http_request: HTTP request (for user info)

    Returns:
        Risk assessment
    """
    try:
        history_db = get_history_db()
        query = history_db.get_query(query_id)
        
        if not query:
            raise HTTPException(status_code=404, detail="Query not found")
        
        # Parse execution_results if it's a string
        execution_results = query.get("execution_results")
        if isinstance(execution_results, str):
            import json
            try:
                execution_results = json.loads(execution_results)
            except:
                execution_results = None
        
        # Calculate risk assessment
        assessment = calculate_risk_assessment(
            query_id=query_id,
            question=query["question"],
            sql_queries=query["sql_queries"],
            confidence=query["confidence"],
            execution_results=execution_results,
            historical_accuracy=None,  # Could be calculated from history in future
        )
        
        # Convert to response model
        return RiskAssessmentResponse(
            overall_risk=assessment["overall_risk"],
            confidence_factors=ConfidenceFactor(**assessment["confidence_factors"]),
            risk_factors=[RiskFactor(**rf) for rf in assessment["risk_factors"]],
            allowed_actions=assessment["allowed_actions"],
            recommended_action=assessment["recommended_action"],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query/{query_id}/escalate")
async def escalate_query(
    query_id: str,
    http_request: Request = None,
) -> dict:
    """
    Escalate a query to expert review.

    Args:
        query_id: Query ID
        http_request: HTTP request (for user info)

    Returns:
        Success message
    """
    try:
        # Get user info
        user = getattr(http_request.state, "user", None) if http_request else None
        user_id = user.get("id") if user else None
        
        # Create a review for this query
        from sputnik.api.db import get_reviews_db
        reviews_db = get_reviews_db()
        
        # Check if review already exists
        existing_reviews = reviews_db.get_reviews()
        existing = next((r for r in existing_reviews if r["query_id"] == query_id), None)
        
        if existing:
            # Update to high priority
            reviews_db.update_review(
                review_id=existing["id"],
                priority="high",
            )
            return {"message": "Query escalated", "review_id": existing["id"]}
        else:
            # Create new review
            review_id = reviews_db.create_review(
                query_id=query_id,
                priority="high",
                submitted_by=user_id,
            )
            return {"message": "Query escalated", "review_id": review_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query/{query_id}/approve")
async def approve_query(
    query_id: str,
    http_request: Request = None,
) -> dict:
    """
    Approve a query (mark as trusted).

    Args:
        query_id: Query ID
        http_request: HTTP request (for user info)

    Returns:
        Success message
    """
    try:
        # In the future, this could update a query approval status
        # For now, just return success
        return {"message": "Query approved", "query_id": query_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query/{query_id}/request-clarification")
async def request_clarification(
    query_id: str,
    clarification: dict,
    http_request: Request = None,
) -> dict:
    """
    Request clarification for a query.

    Args:
        query_id: Query ID
        clarification: Clarification request details
        http_request: HTTP request (for user info)

    Returns:
        Success message
    """
    try:
        # In the future, this could create a clarification request
        # For now, just return success
        return {
            "message": "Clarification requested",
            "query_id": query_id,
            "clarification": clarification,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
