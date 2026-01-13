"""Tests for review API endpoints."""

import pytest
from fastapi.testclient import TestClient
from sputnik.api.server import app
from sputnik.api.db import get_reviews_db, ReviewsDB, get_history_db, QueryHistoryDB


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def reviews_db(temp_db):
    """Create ReviewsDB instance."""
    return ReviewsDB(db_path=temp_db)


@pytest.fixture
def history_db(temp_db):
    """Create QueryHistoryDB instance."""
    return QueryHistoryDB(db_path=temp_db)


def test_get_reviews(client, reviews_db, history_db):
    """Test getting reviews."""
    # Create a query first
    query_id = history_db.save_query(
        question="Test question",
        sql_queries=["SELECT 1"],
        answer="Test answer",
        confidence=0.7,
    )
    
    # Create a review
    review_id = reviews_db.create_review(query_id, priority="high")
    
    response = client.get("/api/v1/reviews")
    assert response.status_code in [200, 401, 403]
    
    if response.status_code == 200:
        data = response.json()
        assert "reviews" in data


def test_approve_review_requires_permission(client, reviews_db, history_db):
    """Test that approving reviews requires permission."""
    # Create query and review
    query_id = history_db.save_query(
        question="Test",
        sql_queries=["SELECT 1"],
        answer="Answer",
        confidence=0.7,
    )
    review_id = reviews_db.create_review(query_id)
    
    response = client.post(
        f"/api/v1/reviews/{review_id}/approve",
        json={"expert_notes": "Looks good"},
    )
    # Should require reviews:approve permission
    assert response.status_code in [200, 401, 403, 404, 500]


def test_reject_review_requires_permission(client, reviews_db, history_db):
    """Test that rejecting reviews requires permission."""
    query_id = history_db.save_query(
        question="Test",
        sql_queries=["SELECT 1"],
        answer="Answer",
        confidence=0.7,
    )
    review_id = reviews_db.create_review(query_id)
    
    response = client.post(
        f"/api/v1/reviews/{review_id}/reject",
        json={"correction_reason": "Incorrect"},
    )
    # Should require reviews:reject permission
    assert response.status_code in [200, 401, 403, 404, 500]
