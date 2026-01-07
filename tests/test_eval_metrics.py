"""Tests for evaluation metrics."""

from sputnik.eval.metrics import (
    compute_accuracy,
    compute_response_quality,
    compute_sql_validity,
)
from sputnik.types import AgentResponse, Rollout, SQLQuery, Token, ToolCall, TrajectoryStep


def test_compute_accuracy() -> None:
    """Test accuracy computation."""
    responses = [
        AgentResponse(
            answer="Answer 1",
            sql_queries=[],
            confidence=0.9,
        ),
        AgentResponse(
            answer="Answer 2",
            sql_queries=[],
            confidence=0.8,
        ),
    ]

    accuracy = compute_accuracy(responses)
    assert 0.0 <= accuracy <= 1.0

    # Empty responses
    assert compute_accuracy([]) == 0.0


def test_compute_sql_validity() -> None:
    """Test SQL validity computation."""
    # Create rollouts with SQL tool calls
    rollout = Rollout(
        query="Test query",
        steps=[
            TrajectoryStep(
                tokens=[Token(text="test", logprob=-0.1)],
                tool_calls=[
                    ToolCall(
                        tool_name="execute_sql",
                        arguments={"query": "SELECT * FROM customers"},
                    )
                ],
                step_index=0,
            )
        ],
        final_answer="Answer",
        metadata={},
    )

    metrics = compute_sql_validity([rollout])

    assert "total_queries" in metrics
    assert "valid_queries" in metrics
    assert "read_only_queries" in metrics
    assert "validity_rate" in metrics
    assert 0.0 <= metrics["validity_rate"] <= 1.0


def test_compute_response_quality() -> None:
    """Test response quality computation."""
    responses = [
        AgentResponse(
            answer="Short answer",
            sql_queries=[],
            confidence=0.9,
            reasoning="Some reasoning",
        ),
        AgentResponse(
            answer="This is a longer answer with more details",
            sql_queries=[],
            confidence=0.8,
        ),
    ]

    quality = compute_response_quality(responses)

    assert "mean_confidence" in quality
    assert "mean_answer_length" in quality
    assert "has_reasoning_rate" in quality

    assert 0.0 <= quality["mean_confidence"] <= 1.0
    assert quality["mean_answer_length"] > 0
    assert 0.0 <= quality["has_reasoning_rate"] <= 1.0

    # Empty responses
    empty_quality = compute_response_quality([])
    assert empty_quality["mean_confidence"] == 0.0
    assert empty_quality["mean_answer_length"] == 0.0

