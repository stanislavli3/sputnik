"""Risk assessment utilities."""

from typing import Dict, List, Any, Optional
from datetime import datetime, timezone


def calculate_risk_assessment(
    query_id: str,
    question: str,
    sql_queries: List[str],
    confidence: float,
    execution_results: Optional[List[Dict[str, Any]]] = None,
    historical_accuracy: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Calculate comprehensive risk assessment for a query.
    
    Args:
        query_id: Query ID
        question: Original question
        sql_queries: Generated SQL queries
        confidence: Query confidence score
        execution_results: Query execution results
        historical_accuracy: Historical accuracy for similar queries (optional)
    
    Returns:
        Risk assessment dictionary
    """
    # Overall risk level based on confidence
    overall_risk = "low"
    if confidence < 0.70:
        overall_risk = "high"
    elif confidence < 0.85:
        overall_risk = "medium"
    
    # Calculate confidence factors
    confidence_factors = {
        "query_interpretation": _assess_query_interpretation(question, sql_queries),
        "data_completeness": _assess_data_completeness(execution_results),
        "schema_match": _assess_schema_match(sql_queries),
        "historical_accuracy": historical_accuracy if historical_accuracy else confidence * 100,
    }
    
    # Identify risk factors
    risk_factors = []
    
    # Low confidence risk
    if confidence < 0.70:
        risk_factors.append({
            "severity": "high",
            "title": "Low Confidence Score",
            "description": f"Query confidence is {confidence * 100:.0f}%, indicating potential inaccuracy",
        })
    elif confidence < 0.85:
        risk_factors.append({
            "severity": "medium",
            "title": "Moderate Confidence",
            "description": f"Query confidence is {confidence * 100:.0f}%, review recommended",
        })
    
    # Query complexity risk
    complexity_score = _assess_query_complexity(sql_queries)
    if complexity_score < 70:
        risk_factors.append({
            "severity": "medium",
            "title": "Complex Query Pattern",
            "description": "Query involves multiple joins or complex aggregations",
        })
    
    # Data completeness risk
    if confidence_factors["data_completeness"] < 80:
        risk_factors.append({
            "severity": "medium",
            "title": "Incomplete Data Coverage",
            "description": "Some data may be missing or filtered out",
        })
    
    # Execution errors
    if execution_results:
        errors = [r for r in execution_results if r.get("error")]
        if errors:
            risk_factors.append({
                "severity": "high",
                "title": "Query Execution Errors",
                "description": f"{len(errors)} query execution error(s) detected",
            })
    
    # Empty results
    if execution_results:
        empty_results = [
            r for r in execution_results 
            if r.get("results") and len(r.get("results", [])) == 0
        ]
        if empty_results and len(empty_results) == len(execution_results):
            risk_factors.append({
                "severity": "medium",
                "title": "No Results Returned",
                "description": "Query executed successfully but returned no data",
            })
    
    # Historical accuracy risk (if available)
    if historical_accuracy and historical_accuracy < 0.80:
        risk_factors.append({
            "severity": "low",
            "title": "Historical Accuracy Concern",
            "description": f"Similar queries have {historical_accuracy * 100:.0f}% accuracy",
        })
    
    # Determine allowed actions based on risk
    allowed_actions = ["accept", "request-clarification", "escalate", "abstain"]
    if overall_risk == "high":
        # High risk: recommend escalation
        recommended_action = "escalate"
    elif overall_risk == "medium":
        # Medium risk: allow all actions
        recommended_action = "request-clarification"
    else:
        # Low risk: can accept
        recommended_action = "accept"
    
    return {
        "overall_risk": overall_risk,
        "confidence_factors": confidence_factors,
        "risk_factors": risk_factors,
        "allowed_actions": allowed_actions,
        "recommended_action": recommended_action,
    }


def _assess_query_interpretation(question: str, sql_queries: List[str]) -> float:
    """Assess how well the question was interpreted into SQL."""
    if not sql_queries:
        return 0.0
    
    # Simple heuristic: check if SQL contains relevant keywords from question
    question_lower = question.lower()
    sql_lower = " ".join(sql_queries).lower()
    
    # Check for common entity matches
    entities = ["customer", "order", "invoice", "product", "vendor", "payment"]
    matches = sum(1 for entity in entities if entity in question_lower and entity in sql_lower)
    
    # Base score
    score = 80.0
    
    # Boost if entities match
    if matches > 0:
        score += min(matches * 5, 15)
    
    # Penalize if SQL seems too generic
    if "SELECT *" in sql_lower and "COUNT(*)" not in sql_lower:
        score -= 10
    
    return min(max(score, 0), 100)


def _assess_data_completeness(execution_results: Optional[List[Dict[str, Any]]]) -> float:
    """Assess data completeness from execution results."""
    if not execution_results:
        return 50.0
    
    # Check for errors
    errors = [r for r in execution_results if r.get("error")]
    if errors:
        return max(100 - (len(errors) * 20), 0)
    
    # Check for empty results
    empty = [r for r in execution_results if r.get("results") and len(r.get("results", [])) == 0]
    if empty:
        return max(100 - (len(empty) * 15), 0)
    
    # If we have results, assume good completeness
    return 90.0


def _assess_schema_match(sql_queries: List[str]) -> float:
    """Assess how well SQL matches expected schema."""
    if not sql_queries:
        return 0.0
    
    sql_lower = " ".join(sql_queries).lower()
    
    # Check for valid SQL structure
    has_select = "select" in sql_lower
    has_from = "from" in sql_lower
    
    if not (has_select and has_from):
        return 0.0
    
    # Check for common table names (good schema match)
    common_tables = ["customers", "orders", "invoices", "products", "inventory"]
    table_matches = sum(1 for table in common_tables if table in sql_lower)
    
    # Base score
    score = 85.0
    
    # Boost if using known tables
    if table_matches > 0:
        score += min(table_matches * 3, 10)
    
    return min(max(score, 0), 100)


def _assess_query_complexity(sql_queries: List[str]) -> float:
    """Assess query complexity (higher = more complex, lower score = simpler)."""
    if not sql_queries:
        return 0.0
    
    sql_lower = " ".join(sql_queries).lower()
    
    complexity_indicators = {
        "join": 20,
        "group by": 15,
        "order by": 5,
        "having": 10,
        "union": 25,
        "subquery": 30,
        "case when": 15,
        "window": 20,
    }
    
    complexity_score = 0
    for indicator, weight in complexity_indicators.items():
        if indicator in sql_lower:
            complexity_score += weight
    
    # Convert to simplicity score (inverse)
    # Higher complexity = lower simplicity score
    if complexity_score == 0:
        return 100  # Very simple
    elif complexity_score < 30:
        return 90  # Simple
    elif complexity_score < 60:
        return 75  # Moderate
    elif complexity_score < 100:
        return 60  # Complex
    else:
        return 40  # Very complex
