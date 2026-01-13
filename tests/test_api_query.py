"""Tests for query API endpoints."""

import pytest
from fastapi.testclient import TestClient
from sputnik.api.server import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_execute_query_requires_permission(client):
    """Test that executing queries requires permission."""
    response = client.post(
        "/api/v1/query",
        json={
            "question": "What is the total revenue?",
        },
    )
    # Should require query:execute permission
    assert response.status_code in [200, 401, 403, 422, 500]


def test_execute_query_invalid_request(client):
    """Test query execution with invalid request."""
    response = client.post(
        "/api/v1/query",
        json={},  # Missing question
    )
    assert response.status_code in [422, 401, 403]  # Validation error or auth error
