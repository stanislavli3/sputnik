"""Evaluation metrics for agent performance."""

from typing import Any, Dict, List, Optional

from sputnik.types import AgentResponse, Rollout


def compute_accuracy(
    responses: List[AgentResponse],
    ground_truth: Optional[List[str]] = None,
) -> float:
    """
    Compute accuracy metric (placeholder for future implementation).

    Args:
        responses: List of agent responses
        ground_truth: Optional ground truth answers

    Returns:
        Accuracy score (0.0 to 1.0)
    """
    if not responses:
        return 0.0

    # Mock implementation: always return 0.5
    # In production, this would compare responses to ground truth
    return 0.5


def compute_sql_validity(rollouts: List[Rollout]) -> Dict[str, Any]:
    """
    Compute SQL validity metrics.

    Args:
        rollouts: List of rollouts to analyze

    Returns:
        Dictionary of SQL validity metrics
    """
    total_queries = 0
    valid_queries = 0
    read_only_queries = 0

    for rollout in rollouts:
        # Extract SQL queries from metadata or tool calls
        # This is a simplified check
        for step in rollout.steps:
            for tool_call in step.tool_calls:
                if tool_call.tool_name == "execute_sql":
                    total_queries += 1
                    # Check if query is read-only (simplified)
                    if "SELECT" in str(tool_call.arguments).upper():
                        read_only_queries += 1
                        valid_queries += 1

    return {
            "total_queries": total_queries,
            "valid_queries": valid_queries,
            "read_only_queries": read_only_queries,
            "validity_rate": valid_queries / total_queries if total_queries > 0 else 0.0,
        }


def compute_response_quality(responses: List[AgentResponse]) -> Dict[str, float]:
    """
    Compute response quality metrics.

    Args:
        responses: List of agent responses

    Returns:
        Dictionary of quality metrics
    """
    if not responses:
        return {
            "mean_confidence": 0.0,
            "mean_answer_length": 0.0,
            "has_reasoning_rate": 0.0,
        }

    confidences = [r.confidence for r in responses]
    answer_lengths = [len(r.answer) for r in responses]
    has_reasoning = [1 if r.reasoning else 0 for r in responses]

    return {
        "mean_confidence": sum(confidences) / len(confidences),
        "mean_answer_length": sum(answer_lengths) / len(answer_lengths),
        "has_reasoning_rate": sum(has_reasoning) / len(has_reasoning),
    }

