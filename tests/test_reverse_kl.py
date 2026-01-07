"""Tests for reverse KL computation."""

from sputnik.distill.reverse_kl import (
    compute_advantage,
    compute_discounted_advantages,
    compute_reverse_kl,
)
from sputnik.types import Token


def test_compute_reverse_kl() -> None:
    """Test reverse KL computation."""
    student_tokens = [
        Token(text="SELECT", logprob=-0.1),
        Token(text="SUM", logprob=-0.2),
        Token(text="total", logprob=-0.3),
    ]

    teacher_logprobs = [-0.15, -0.25, -0.35]

    reverse_kls = compute_reverse_kl(student_tokens, teacher_logprobs)

    assert len(reverse_kls) == 3
    # reverse_kl = student - teacher
    assert abs(reverse_kls[0] - (-0.1 - (-0.15))) < 1e-6  # 0.05
    assert abs(reverse_kls[1] - (-0.2 - (-0.25))) < 1e-6  # 0.05
    assert abs(reverse_kls[2] - (-0.3 - (-0.35))) < 1e-6  # 0.05


def test_compute_reverse_kl_mismatch() -> None:
    """Test that mismatched lengths raise errors."""
    student_tokens = [Token(text="test", logprob=-0.1)]
    teacher_logprobs = [-0.1, -0.2]

    try:
        compute_reverse_kl(student_tokens, teacher_logprobs)
        assert False, "Should raise ValueError"
    except ValueError:
        pass


def test_compute_advantage() -> None:
    """Test advantage computation."""
    reverse_kls = [0.1, -0.2, 0.05]
    advantages = compute_advantage(reverse_kls)

    assert len(advantages) == 3
    assert advantages[0] == -0.1
    assert advantages[1] == 0.2
    assert advantages[2] == -0.05


def test_compute_discounted_advantages_zero_discount() -> None:
    """Test discounted advantages with zero discount factor."""
    advantages = [0.1, 0.2, 0.3]
    discounted = compute_discounted_advantages(advantages, discount_factor=0.0)

    # With discount=0, should be the same
    assert discounted == advantages


def test_compute_discounted_advantages_with_discount() -> None:
    """Test discounted advantages with non-zero discount."""
    advantages = [1.0, 1.0, 1.0]
    discounted = compute_discounted_advantages(advantages, discount_factor=0.5)

    assert len(discounted) == 3
    # First should be full value, subsequent should be discounted
    assert abs(discounted[0] - 1.0) < 1e-6
    assert abs(discounted[1] - 0.5) < 1e-6
    assert abs(discounted[2] - 0.25) < 1e-6

