"""Core type definitions for Sputnik."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence

from pydantic import BaseModel


@dataclass
class Token:
    """A single token with its log probability."""

    text: str
    logprob: float
    token_id: Optional[int] = None


@dataclass
class ToolCall:
    """A tool call made during agent execution."""

    tool_name: str
    arguments: Dict[str, Any]
    result: Optional[Any] = None
    timestamp: Optional[float] = None


@dataclass
class TrajectoryStep:
    """A single step in an agent trajectory."""

    tokens: List[Token]
    tool_calls: List[ToolCall]
    step_index: int


@dataclass
class Rollout:
    """A complete agent rollout (trajectory)."""

    query: str
    steps: List[TrajectoryStep]
    final_answer: str
    metadata: Dict[str, Any]


class SQLQuery(BaseModel):
    """A validated SQL query."""

    query: str
    is_read_only: bool = True
    estimated_cost: Optional[float] = None

    class Config:
        frozen = True


class ERPSchema(BaseModel):
    """Schema information for an ERP system."""

    tables: Dict[str, List[str]]  # table_name -> [column_name, ...]
    relationships: List[Dict[str, str]]  # [{from_table, from_col, to_table, to_col}, ...]

    class Config:
        frozen = True


class AgentResponse(BaseModel):
    """Response from the agent."""

    answer: str
    sql_queries: List[SQLQuery]
    confidence: float
    reasoning: Optional[str] = None

    class Config:
        frozen = True

