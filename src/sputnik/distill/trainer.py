"""Training loop for on-policy distillation."""

from typing import List, Optional

from sputnik.distill.reverse_kl import compute_discounted_advantages, compute_reverse_kl
from sputnik.distill.teacher import Teacher
from sputnik.types import Rollout, Token


class DistillationTrainer:
    """Trainer for on-policy distillation."""

    def __init__(
        self,
        teacher: Teacher,
        discount_factor: float = 0.0,
    ) -> None:
        """
        Initialize the distillation trainer.

        Args:
            teacher: Teacher model for scoring
            discount_factor: Discount factor for advantages (0 = next-token optimization)
        """
        self.teacher = teacher
        self.discount_factor = discount_factor

    def compute_training_signal(
        self,
        rollout: Rollout,
    ) -> List[float]:
        """
        Compute training signal (discounted advantages) for a rollout.

        Args:
            rollout: Agent rollout to compute signal for

        Returns:
            List of training signals (one per token across all steps)
        """
        all_tokens: List[Token] = []
        for step in rollout.steps:
            all_tokens.extend(step.tokens)

        if not all_tokens:
            return []

        # Get teacher scores
        context = rollout.query
        teacher_logprobs = self.teacher.score_tokens(all_tokens, context)

        # Compute reverse KL
        reverse_kls = compute_reverse_kl(all_tokens, teacher_logprobs)

        # Compute advantages
        advantages = [-rkl for rkl in reverse_kls]

        # Apply discounting
        discounted_advantages = compute_discounted_advantages(advantages, self.discount_factor)

        return discounted_advantages

    def train_step(self, rollouts: List[Rollout]) -> dict:
        """
        Perform one training step on a batch of rollouts.

        Args:
            rollouts: List of rollouts to train on

        Returns:
            Training metrics dictionary
        """
        all_signals: List[float] = []
        total_tokens = 0

        for rollout in rollouts:
            signals = self.compute_training_signal(rollout)
            all_signals.extend(signals)
            total_tokens += sum(len(step.tokens) for step in rollout.steps)

        if not all_signals:
            return {"loss": 0.0, "mean_advantage": 0.0, "total_tokens": 0}

        # In a real implementation, this would update model weights
        # For now, just compute metrics
        mean_advantage = sum(all_signals) / len(all_signals)
        # Loss would be negative advantage (we want to maximize advantage)
        loss = -mean_advantage

        return {
            "loss": loss,
            "mean_advantage": mean_advantage,
            "total_tokens": total_tokens,
            "num_rollouts": len(rollouts),
        }

