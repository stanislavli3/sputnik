"""Metrics calculation utilities."""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from sputnik.api.db import get_history_db, get_reviews_db


def calculate_metrics(period_days: int = 90) -> Dict[str, Any]:
    """
    Calculate reliability metrics for a given period.
    
    Args:
        period_days: Number of days to look back
    
    Returns:
        Dictionary with all metrics
    """
    history_db = get_history_db()
    reviews_db = get_reviews_db()
    
    # Get date threshold
    cutoff_date = datetime.utcnow() - timedelta(days=period_days)
    
    # Get all queries in period
    all_queries = history_db.get_query_history(page=1, page_size=10000)
    queries = [
        q for q in all_queries["queries"]
        if q.get("created_at") and datetime.fromisoformat(q["created_at"].replace("Z", "+00:00")) >= cutoff_date
    ]
    
    # Get all reviews
    all_reviews = reviews_db.get_reviews()
    
    # Calculate primary metrics
    total_queries = len(queries)
    if total_queries == 0:
        return _get_empty_metrics()
    
    # Auto-answer rate: queries that didn't need review (confidence >= 0.75)
    auto_answered = sum(1 for q in queries if q.get("confidence", 0) >= 0.75)
    auto_answer_rate = (auto_answered / total_queries) * 100 if total_queries > 0 else 0
    
    # Expert intervention: queries that had reviews
    reviewed_queries = {r["query_id"] for r in all_reviews}
    expert_intervention = (len(reviewed_queries) / total_queries) * 100 if total_queries > 0 else 0
    
    # Error recurrence: queries with errors in execution_results
    error_queries = sum(
        1 for q in queries
        if q.get("execution_results") and any(
            r.get("error") for r in (q["execution_results"] if isinstance(q["execution_results"], list) else [])
        )
    )
    error_recurrence = (error_queries / total_queries) * 100 if total_queries > 0 else 0
    
    # Average confidence
    confidences = [q.get("confidence", 0) for q in queries if q.get("confidence")]
    avg_confidence = (sum(confidences) / len(confidences) * 100) if confidences else 0
    
    # Trust score: combination of metrics
    trust_score = (
        (auto_answer_rate * 0.4) +
        ((100 - expert_intervention) * 0.3) +
        ((100 - error_recurrence * 10) * 0.2) +
        (avg_confidence * 0.1)
    )
    trust_score = max(0, min(100, trust_score))
    
    # Calculate trends (compare with previous period)
    previous_cutoff = cutoff_date - timedelta(days=period_days)
    previous_queries = [
        q for q in all_queries["queries"]
        if q.get("created_at") and 
        previous_cutoff <= datetime.fromisoformat(q["created_at"].replace("Z", "+00:00")) < cutoff_date
    ]
    
    prev_auto_answer = (sum(1 for q in previous_queries if q.get("confidence", 0) >= 0.75) / len(previous_queries) * 100) if previous_queries else 0
    prev_intervention = (len({r["query_id"] for r in all_reviews if r.get("created_at") and datetime.fromisoformat(r["created_at"].replace("Z", "+00:00")) < cutoff_date}) / len(previous_queries) * 100) if previous_queries else 0
    prev_error = (sum(1 for q in previous_queries if q.get("execution_results") and any(r.get("error") for r in (q["execution_results"] if isinstance(q["execution_results"], list) else []))) / len(previous_queries) * 100) if previous_queries else 0
    prev_confidence = (sum(q.get("confidence", 0) for q in previous_queries if q.get("confidence")) / len(previous_queries) * 100) if previous_queries else 0
    
    # Calculate trends
    auto_answer_trend = auto_answer_rate - prev_auto_answer
    intervention_trend = expert_intervention - prev_intervention
    error_trend = error_recurrence - prev_error
    confidence_trend = avg_confidence - prev_confidence
    
    # Trust score trend (weekly for last 12 weeks)
    trust_trend = _calculate_trust_trend(queries, all_reviews, period_days)
    
    return {
        "auto_answer_rate": round(auto_answer_rate, 1),
        "expert_intervention": round(expert_intervention, 1),
        "error_recurrence": round(error_recurrence, 1),
        "avg_confidence": round(avg_confidence, 1),
        "trust_score": round(trust_score, 1),
        "trends": {
            "auto_answer_rate": round(auto_answer_trend, 1),
            "expert_intervention": round(intervention_trend, 1),
            "error_recurrence": round(error_trend, 1),
            "avg_confidence": round(confidence_trend, 1),
        },
        "trust_trend": trust_trend,
    }


def calculate_category_metrics(period_days: int = 90) -> List[Dict[str, Any]]:
    """
    Calculate metrics by query category.
    
    Args:
        period_days: Number of days to look back
    
    Returns:
        List of category metrics
    """
    history_db = get_history_db()
    all_queries = history_db.get_query_history(page=1, page_size=10000)
    cutoff_date = datetime.utcnow() - timedelta(days=period_days)
    
    queries = [
        q for q in all_queries["queries"]
        if q.get("created_at") and datetime.fromisoformat(q["created_at"].replace("Z", "+00:00")) >= cutoff_date
    ]
    
    # Categorize queries by keywords in question
    categories = defaultdict(lambda: {"queries": [], "count": 0})
    
    for query in queries:
        question = query.get("question", "").lower()
        category = _categorize_query(question)
        categories[category]["queries"].append(query)
        categories[category]["count"] += 1
    
    # Calculate accuracy for each category
    category_metrics = []
    for category, data in categories.items():
        queries_in_category = data["queries"]
        if not queries_in_category:
            continue
        
        # Accuracy = average confidence
        confidences = [q.get("confidence", 0) for q in queries_in_category if q.get("confidence")]
        accuracy = (sum(confidences) / len(confidences) * 100) if confidences else 0
        
        category_metrics.append({
            "category": category,
            "queries": len(queries_in_category),
            "accuracy": round(accuracy, 1),
        })
    
    # Sort by query count
    category_metrics.sort(key=lambda x: x["queries"], reverse=True)
    
    return category_metrics


def calculate_expert_corrections(period_days: int = 90) -> List[Dict[str, Any]]:
    """
    Calculate expert correction statistics.
    
    Args:
        period_days: Number of days to look back
    
    Returns:
        List of correction type metrics
    """
    reviews_db = get_reviews_db()
    all_reviews = reviews_db.get_reviews()
    
    cutoff_date = datetime.utcnow() - timedelta(days=period_days)
    reviews = [
        r for r in all_reviews
        if r.get("created_at") and datetime.fromisoformat(r["created_at"].replace("Z", "+00:00")) >= cutoff_date
    ]
    
    # Group by correction reason
    corrections = defaultdict(lambda: {"count": 0, "learned": 0})
    
    for review in reviews:
        reason = review.get("correction_reason") or "unknown"
        corrections[reason]["count"] += 1
        
        # Consider "learned" if review was approved and has notes
        if review.get("status") == "approved" and review.get("expert_notes"):
            corrections[reason]["learned"] += 1
    
    # Convert to list
    correction_metrics = []
    for reason, data in corrections.items():
        # Map reason codes to display names
        display_name = _map_reason_code(reason)
        learned_ratio = (data["learned"] / data["count"]) if data["count"] > 0 else 0
        
        if learned_ratio >= 0.8:
            impact = "learned"
        elif learned_ratio >= 0.5:
            impact = "partial"
        else:
            impact = "pending"
        
        correction_metrics.append({
            "type": display_name,
            "count": data["count"],
            "impact": impact,
        })
    
    # Sort by count
    correction_metrics.sort(key=lambda x: x["count"], reverse=True)
    
    return correction_metrics


def _categorize_query(question: str) -> str:
    """Categorize a query based on keywords."""
    question_lower = question.lower()
    
    if any(word in question_lower for word in ["ap", "ar", "accounts payable", "accounts receivable", "balance", "outstanding"]):
        return "AP/AR Balances"
    elif any(word in question_lower for word in ["gl", "general ledger", "reconciliation", "reconcile"]):
        return "GL Reconciliation"
    elif any(word in question_lower for word in ["cost", "cogs", "expense", "spend"]):
        return "Cost Analysis"
    elif any(word in question_lower for word in ["revenue", "sales", "income", "recognition"]):
        return "Revenue Recognition"
    elif any(word in question_lower for word in ["intercompany", "inter-company", "transfer"]):
        return "Intercompany"
    elif any(word in question_lower for word in ["inventory", "stock", "warehouse"]):
        return "Inventory"
    elif any(word in question_lower for word in ["customer", "client"]):
        return "Customer Data"
    elif any(word in question_lower for word in ["order", "purchase"]):
        return "Orders"
    else:
        return "Other"


def _map_reason_code(reason: str) -> str:
    """Map reason code to display name."""
    mapping = {
        "data-scope": "Data Scope",
        "methodology": "Methodology",
        "business-rule": "Business Rule",
        "temporal": "Temporal",
        "expert-edit": "Expert Edit",
        "unknown": "Other",
    }
    return mapping.get(reason, reason.title())


def _calculate_trust_trend(queries: List[Dict], reviews: List[Dict], period_days: int) -> List[float]:
    """Calculate trust score trend over time (weekly)."""
    if not queries:
        return [0] * 12
    
    # Group queries by week
    weekly_data = defaultdict(lambda: {"queries": [], "reviews": []})
    
    for query in queries:
        if not query.get("created_at"):
            continue
        try:
            date = datetime.fromisoformat(query["created_at"].replace("Z", "+00:00"))
            week_num = (datetime.utcnow() - date).days // 7
            if 0 <= week_num < 12:
                weekly_data[week_num]["queries"].append(query)
        except:
            continue
    
    for review in reviews:
        if not review.get("created_at"):
            continue
        try:
            date = datetime.fromisoformat(review["created_at"].replace("Z", "+00:00"))
            week_num = (datetime.utcnow() - date).days // 7
            if 0 <= week_num < 12:
                weekly_data[week_num]["reviews"].append(review)
        except:
            continue
    
    # Calculate trust score for each week
    trend = []
    for week in range(12):
        week_queries = weekly_data[week]["queries"]
        week_reviews = weekly_data[week]["reviews"]
        
        if not week_queries:
            trend.append(0)
            continue
        
        auto_answer = sum(1 for q in week_queries if q.get("confidence", 0) >= 0.75) / len(week_queries) * 100
        intervention = len(set(r["query_id"] for r in week_reviews)) / len(week_queries) * 100 if week_queries else 0
        avg_conf = sum(q.get("confidence", 0) for q in week_queries if q.get("confidence")) / len(week_queries) * 100 if week_queries else 0
        
        trust = (auto_answer * 0.4) + ((100 - intervention) * 0.3) + (avg_conf * 0.3)
        trend.append(max(0, min(100, trust)))
    
    # Reverse to show oldest to newest
    return list(reversed(trend)) if trend else [0] * 12


def _get_empty_metrics() -> Dict[str, Any]:
    """Return empty metrics structure."""
    return {
        "auto_answer_rate": 0.0,
        "expert_intervention": 0.0,
        "error_recurrence": 0.0,
        "avg_confidence": 0.0,
        "trust_score": 0.0,
        "trends": {
            "auto_answer_rate": 0.0,
            "expert_intervention": 0.0,
            "error_recurrence": 0.0,
            "avg_confidence": 0.0,
        },
        "trust_trend": [0] * 12,
    }
