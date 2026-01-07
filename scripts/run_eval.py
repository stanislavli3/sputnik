"""Evaluation script for Sputnik."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sputnik.eval.runner import EvalRunner
from sputnik.types import AgentResponse, SQLQuery


def main() -> None:
    """Run evaluation."""
    print("Running Sputnik evaluation...")
    print()

    # Mock evaluation data
    responses = [
        AgentResponse(
            answer="Total revenue is $8,851.25",
            sql_queries=[SQLQuery(query="SELECT SUM(total_amount) FROM orders", is_read_only=True)],
            confidence=0.9,
        ),
        AgentResponse(
            answer="There are 3 customers",
            sql_queries=[SQLQuery(query="SELECT COUNT(*) FROM customers", is_read_only=True)],
            confidence=0.85,
        ),
    ]

    # Mock rollouts (simplified)
    from sputnik.types import Rollout, Token, TrajectoryStep

    rollouts = [
        Rollout(
            query="What is the total revenue?",
            steps=[
                TrajectoryStep(
                    tokens=[Token(text="SELECT", logprob=-0.1), Token(text="SUM", logprob=-0.2)],
                    tool_calls=[],
                    step_index=0,
                )
            ],
            final_answer="Total revenue is $8,851.25",
            metadata={},
        )
    ]

    runner = EvalRunner()
    metrics = runner.run(responses, rollouts)

    print("Evaluation Results:")
    print(f"  Accuracy: {metrics['accuracy']:.2%}")
    print(f"  SQL Validity Rate: {metrics['sql_validity']['validity_rate']:.2%}")
    print(f"  Mean Confidence: {metrics['response_quality']['mean_confidence']:.2f}")
    print(f"  Number of Examples: {metrics['num_examples']}")


if __name__ == "__main__":
    main()

