"""Tests for rollout serialization and collection."""

from sputnik.distill.rollout_collector import RolloutBuilder, RolloutCollector
from sputnik.types import Rollout, Token, ToolCall, TrajectoryStep


def test_rollout_builder() -> None:
    """Test RolloutBuilder functionality."""
    builder = RolloutBuilder("What is the total revenue?")

    # Add tokens
    tokens = [
        Token(text="SELECT", logprob=-0.1),
        Token(text="SUM", logprob=-0.2),
    ]
    builder.add_step(tokens)

    # Add step with tool call
    tool_call = ToolCall(
        tool_name="execute_sql",
        arguments={"query": "SELECT SUM(total_amount) FROM orders"},
    )
    builder.add_step([Token(text="FROM", logprob=-0.1)], tool_calls=[tool_call])

    builder.set_final_answer("Total revenue is $8,851.25")
    builder.add_metadata("confidence", 0.9)

    rollout = builder.build()

    assert rollout.query == "What is the total revenue?"
    assert len(rollout.steps) == 2
    assert rollout.final_answer == "Total revenue is $8,851.25"
    assert rollout.metadata["confidence"] == 0.9


def test_rollout_collector() -> None:
    """Test RolloutCollector functionality."""
    collector = RolloutCollector()

    # Create a rollout
    builder = collector.start_rollout("Test query")
    builder.add_step([Token(text="test", logprob=-0.1)])
    builder.set_final_answer("Test answer")
    rollout = builder.build()

    collector.add_rollout(rollout)

    rollouts = collector.get_rollouts()
    assert len(rollouts) == 1
    assert rollouts[0].query == "Test query"

    collector.clear()
    assert len(collector.get_rollouts()) == 0


def test_rollout_incomplete() -> None:
    """Test that incomplete rollouts raise errors."""
    builder = RolloutBuilder("Test")

    # Missing final answer
    builder.add_step([Token(text="test", logprob=-0.1)])
    try:
        builder.build()
        assert False, "Should raise ValueError"
    except ValueError:
        pass

    # Missing steps
    builder2 = RolloutBuilder("Test")
    builder2.set_final_answer("Answer")
    try:
        builder2.build()
        assert False, "Should raise ValueError"
    except ValueError:
        pass

