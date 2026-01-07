"""Teacher model interface for scoring student trajectories."""

from typing import List

from sputnik.types import Token


class Teacher:
    """Interface for teacher models that score student tokens."""

    def score_tokens(self, tokens: List[Token], context: str) -> List[float]:
        """
        Score a sequence of tokens with per-token log probabilities.

        Args:
            tokens: List of tokens to score
            context: Context string (e.g., the query being answered)

        Returns:
            List of log probabilities, one per token
        """
        raise NotImplementedError


class MockTeacher(Teacher):
    """Mock teacher that returns deterministic fake logprobs."""

    def __init__(self, base_logprob: float = -0.5) -> None:
        """
        Initialize the mock teacher.

        Args:
            base_logprob: Base log probability to return
        """
        self.base_logprob = base_logprob

    def score_tokens(self, tokens: List[Token], context: str) -> List[float]:
        """
        Score tokens with deterministic fake logprobs.

        Args:
            tokens: List of tokens to score
            context: Context string (ignored in mock)

        Returns:
            List of fake log probabilities
        """
        # Deterministic: hash-based pseudo-logprobs
        # In production, this would call a real teacher model API
        logprobs: List[float] = []
        for i, token in enumerate(tokens):
            # Simple hash-based deterministic "logprob"
            token_hash = hash(token.text) % 1000
            # Normalize to reasonable logprob range
            fake_logprob = self.base_logprob + (token_hash / 10000.0) - 0.05
            logprobs.append(fake_logprob)

        return logprobs

