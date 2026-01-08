"""Rollout endpoints."""

from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from sputnik.distill.rollout_collector import RolloutCollector
from sputnik.distill.teacher import MockTeacher
from sputnik.distill.trainer import DistillationTrainer
from sputnik.types import Rollout

router = APIRouter()

# Global collector (in production, use dependency injection)
_collector: Optional[RolloutCollector] = None
_trainer: Optional[DistillationTrainer] = None


def get_collector() -> RolloutCollector:
    """Get or create the rollout collector."""
    global _collector
    if _collector is None:
        _collector = RolloutCollector()
    return _collector


def get_trainer() -> DistillationTrainer:
    """Get or create the trainer."""
    global _trainer
    if _trainer is None:
        teacher = MockTeacher()
        _trainer = DistillationTrainer(teacher, discount_factor=0.0)
    return _trainer


class RolloutResponse(BaseModel):
    """Rollout response model."""

    id: str
    query: str
    final_answer: str
    num_steps: int
    num_tokens: int


class RolloutsListResponse(BaseModel):
    """Rollouts list response model."""

    rollouts: List[RolloutResponse]
    total: int


@router.get("/rollouts", response_model=RolloutsListResponse)
async def list_rollouts() -> RolloutsListResponse:
    """
    List all collected rollouts.

    Returns:
        List of rollouts
    """
    try:
        collector = get_collector()
        rollouts = collector.get_rollouts()

        rollout_responses = [
            RolloutResponse(
                id=f"rollout_{i}",
                query=r.query,
                final_answer=r.final_answer,
                num_steps=len(r.steps),
                num_tokens=sum(len(step.tokens) for step in r.steps),
            )
            for i, r in enumerate(rollouts)
        ]

        return RolloutsListResponse(rollouts=rollout_responses, total=len(rollout_responses))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rollouts/train")
async def train_on_rollouts() -> dict:
    """
    Train on collected rollouts.

    Returns:
        Training metrics
    """
    try:
        collector = get_collector()
        trainer = get_trainer()

        rollouts = collector.get_rollouts()
        if not rollouts:
            return {"message": "No rollouts to train on", "metrics": {}}

        metrics = trainer.train_step(rollouts)

        return {"message": "Training complete", "metrics": metrics}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

