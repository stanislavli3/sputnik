"""Evaluation runner for testing agent performance."""

from typing import Any, Dict, List, Optional

from sputnik.eval.metrics import compute_accuracy, compute_response_quality, compute_sql_validity
from sputnik.types import AgentResponse, Rollout


class EvalRunner:
    """Runner for evaluation benchmarks."""

    def __init__(self) -> None:
        """Initialize the evaluation runner."""
        pass

    def run(
        self,
        responses: List[AgentResponse],
        rollouts: List[Rollout],
        ground_truth: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Run evaluation on a set of responses and rollouts.

        Args:
            responses: List of agent responses
            rollouts: List of corresponding rollouts
            ground_truth: Optional ground truth answers

        Returns:
            Dictionary of evaluation metrics
        """
        accuracy = compute_accuracy(responses, ground_truth)
        sql_metrics = compute_sql_validity(rollouts)
        quality_metrics = compute_response_quality(responses)

        return {
            "accuracy": accuracy,
            "sql_validity": sql_metrics,
            "response_quality": quality_metrics,
            "num_examples": len(responses),
        }

