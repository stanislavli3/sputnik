"""On-policy distillation training script."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sputnik.distill.rollout_collector import RolloutCollector
from sputnik.distill.teacher import MockTeacher
from sputnik.distill.trainer import DistillationTrainer
from sputnik.types import Rollout, Token, ToolCall, TrajectoryStep


def generate_mock_rollout(query: str) -> Rollout:
    """
    Generate a mock rollout for demonstration.

    Args:
        query: Business question

    Returns:
        Mock rollout
    """
    # Generate deterministic tokens with fake logprobs
    tokens = [
        Token(text="SELECT", logprob=-0.1),
        Token(text="SUM", logprob=-0.2),
        Token(text="(", logprob=-0.05),
        Token(text="total_amount", logprob=-0.3),
        Token(text=")", logprob=-0.05),
        Token(text="FROM", logprob=-0.1),
        Token(text="orders", logprob=-0.2),
    ]

    tool_calls = [
        ToolCall(
            tool_name="execute_sql",
            arguments={"query": "SELECT SUM(total_amount) FROM orders"},
        )
    ]

    step = TrajectoryStep(tokens=tokens, tool_calls=tool_calls, step_index=0)

    return Rollout(
        query=query,
        steps=[step],
        final_answer=f"Answer to: {query}",
        metadata={},
    )


def main() -> None:
    """Run on-policy distillation training."""
    print("=" * 60)
    print("Sputnik: On-Policy Distillation Training")
    print("=" * 60)
    print()

    # Initialize components
    teacher = MockTeacher(base_logprob=-0.5)
    trainer = DistillationTrainer(teacher, discount_factor=0.0)
    collector = RolloutCollector()

    # Generate mock rollouts
    queries = [
        "What is the total revenue?",
        "How many customers do we have?",
        "What is our inventory status?",
    ]

    print("Collecting rollouts...")
    for query in queries:
        rollout = generate_mock_rollout(query)
        collector.add_rollout(rollout)
        print(f"  ✓ Collected rollout for: {query}")

    rollouts = collector.get_rollouts()
    print(f"\nCollected {len(rollouts)} rollouts")
    print()

    # Compute training signals
    print("Computing training signals...")
    for i, rollout in enumerate(rollouts, 1):
        signals = trainer.compute_training_signal(rollout)
        mean_signal = sum(signals) / len(signals) if signals else 0.0
        print(f"  Rollout {i}: {len(signals)} tokens, mean advantage: {mean_signal:.4f}")

    print()

    # Training step
    print("Running training step...")
    metrics = trainer.train_step(rollouts)
    print(f"  Loss: {metrics['loss']:.4f}")
    print(f"  Mean Advantage: {metrics['mean_advantage']:.4f}")
    print(f"  Total Tokens: {metrics['total_tokens']}")
    print(f"  Number of Rollouts: {metrics['num_rollouts']}")

    print()
    print("Training complete!")
    print()
    print("Note: This is a skeleton implementation with mock components.")
    print("In production, this would:")
    print("  - Use real student/teacher models")
    print("  - Update model weights via backpropagation")
    print("  - Save checkpoints and metrics")


if __name__ == "__main__":
    main()

