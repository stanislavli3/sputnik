"""Metrics endpoints."""

from typing import Optional, Dict, Any
from time import time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from sputnik.api.metrics import (
    calculate_metrics,
    calculate_category_metrics,
    calculate_expert_corrections,
)
from sputnik.api.cache import get_metrics_cache

router = APIRouter()
cache = get_metrics_cache()


class MetricsOverview(BaseModel):
    """Metrics overview model."""

    auto_answer_rate: float
    expert_intervention: float
    error_recurrence: float
    avg_confidence: float
    trust_score: float
    trends: dict
    trust_trend: list[float]


class CategoryMetric(BaseModel):
    """Category metric model."""

    category: str
    queries: int
    accuracy: float


class ExpertCorrection(BaseModel):
    """Expert correction metric model."""

    type: str
    count: int
    impact: str


@router.get("/metrics/overview", response_model=MetricsOverview)
async def get_metrics_overview(period: str = "90d") -> MetricsOverview:
    """
    Get overall reliability metrics.

    Args:
        period: Time period (e.g., "90d", "30d", "7d")

    Returns:
        Metrics overview
    """
    try:
        # Check cache
        cache_key = f"overview_{period}"
        cached = cache.get(cache_key)
        if cached:
            return MetricsOverview(**cached)
        
        # Parse period
        period_days = _parse_period(period)
        
        metrics = calculate_metrics(period_days=period_days)
        
        # Cache result
        cache.set(cache_key, metrics, ttl=60)  # 1 minute TTL
        
        return MetricsOverview(**metrics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/by-category", response_model=list[CategoryMetric])
async def get_category_metrics(period: str = "90d") -> list[CategoryMetric]:
    """
    Get metrics by query category.

    Args:
        period: Time period (e.g., "90d", "30d", "7d")

    Returns:
        List of category metrics
    """
    try:
        # Check cache
        cache_key = f"category_{period}"
        cached = _get_cached(cache_key)
        if cached:
            return [CategoryMetric(**m) for m in cached]
        
        period_days = _parse_period(period)
        metrics = calculate_category_metrics(period_days=period_days)
        
        # Cache result
        cache.set(cache_key, metrics, ttl=60)  # 1 minute TTL
        
        return [CategoryMetric(**m) for m in metrics]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/expert-corrections", response_model=list[ExpertCorrection])
async def get_expert_corrections(period: str = "90d") -> list[ExpertCorrection]:
    """
    Get expert correction statistics.

    Args:
        period: Time period (e.g., "90d", "30d", "7d")

    Returns:
        List of correction metrics
    """
    try:
        # Check cache
        cache_key = f"corrections_{period}"
        cached = cache.get(cache_key)
        if cached:
            return [ExpertCorrection(**c) for c in cached]
        
        period_days = _parse_period(period)
        corrections = calculate_expert_corrections(period_days=period_days)
        
        # Cache result
        cache.set(cache_key, corrections, ttl=60)  # 1 minute TTL
        
        return [ExpertCorrection(**c) for c in corrections]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _parse_period(period: str) -> int:
    """Parse period string to days."""
    period = period.lower().strip()
    
    if period.endswith("d"):
        return int(period[:-1])
    elif period.endswith("w"):
        return int(period[:-1]) * 7
    elif period.endswith("m"):
        return int(period[:-1]) * 30
    elif period.endswith("y"):
        return int(period[:-1]) * 365
    else:
        # Default to 90 days
        return 90
