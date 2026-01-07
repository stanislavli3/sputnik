"""Rollout collection for on-policy distillation."""

from typing import Any, List, Optional

from sputnik.types import Rollout, Token, ToolCall, TrajectoryStep


class RolloutCollector:
    """Collects agent rollouts for training."""

    def __init__(self) -> None:
        """Initialize the rollout collector."""
        self.rollouts: List[Rollout] = []

    def start_rollout(self, query: str) -> "RolloutBuilder":
        """
        Start collecting a new rollout.

        Args:
            query: The business question being answered

        Returns:
            RolloutBuilder for building the rollout
        """
        return RolloutBuilder(query)

    def add_rollout(self, rollout: Rollout) -> None:
        """
        Add a completed rollout to the collection.

        Args:
            rollout: Completed rollout
        """
        self.rollouts.append(rollout)

    def get_rollouts(self) -> List[Rollout]:
        """
        Get all collected rollouts.

        Returns:
            List of rollouts
        """
        return self.rollouts.copy()

    def clear(self) -> None:
        """Clear all collected rollouts."""
        self.rollouts.clear()


class RolloutBuilder:
    """Builder for constructing a rollout."""

    def __init__(self, query: str) -> None:
        """
        Initialize the rollout builder.

        Args:
            query: The business question
        """
        self.query = query
        self.steps: List[TrajectoryStep] = []
        self.current_step_index = 0
        self.final_answer: Optional[str] = None
        self.metadata: dict = {}

    def add_step(
        self,
        tokens: List[Token],
        tool_calls: Optional[List[ToolCall]] = None,
    ) -> None:
        """
        Add a step to the rollout.

        Args:
            tokens: Tokens generated in this step
            tool_calls: Optional tool calls made in this step
        """
        step = TrajectoryStep(
            tokens=tokens,
            tool_calls=tool_calls or [],
            step_index=self.current_step_index,
        )
        self.steps.append(step)
        self.current_step_index += 1

    def set_final_answer(self, answer: str) -> None:
        """
        Set the final answer for the rollout.

        Args:
            answer: Final answer text
        """
        self.final_answer = answer

    def add_metadata(self, key: str, value: Any) -> None:
        """
        Add metadata to the rollout.

        Args:
            key: Metadata key
            value: Metadata value
        """
        self.metadata[key] = value

    def build(self) -> Rollout:
        """
        Build the final rollout.

        Returns:
            Completed Rollout object

        Raises:
            ValueError: If rollout is incomplete
        """
        if not self.steps:
            raise ValueError("Rollout must have at least one step")
        if self.final_answer is None:
            raise ValueError("Rollout must have a final answer")

        return Rollout(
            query=self.query,
            steps=self.steps,
            final_answer=self.final_answer,
            metadata=self.metadata,
        )

