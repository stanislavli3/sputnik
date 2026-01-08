"""Query endpoints."""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from sputnik.agent.planner import Planner
from sputnik.agent.sql_generator import SQLGenerator
from sputnik.env.duckdb_env import DuckDBEnv
from sputnik.types import AgentResponse, SQLQuery

router = APIRouter()

# Global environment (in production, use dependency injection)
_env: Optional[DuckDBEnv] = None


def get_env() -> DuckDBEnv:
    """Get or create the DuckDB environment."""
    global _env
    if _env is None:
        _env = DuckDBEnv("demo_erp.duckdb")
    return _env


class QueryRequest(BaseModel):
    """Query request model."""

    question: str
    context: Optional[List[str]] = None


class QueryResponse(BaseModel):
    """Query response model."""

    answer: str
    sql_queries: List[str]
    confidence: float
    reasoning: Optional[str] = None
    execution_results: Optional[List[dict]] = None


@router.post("/query", response_model=QueryResponse)
async def execute_query(
    request: QueryRequest,
    http_request: Request,
) -> QueryResponse:
    """
    Execute a natural language query.

    Args:
        request: Query request with question
        http_request: HTTP request (for user info)

    Returns:
        Query response with answer and SQL queries
    """
    # Access authenticated user if available
    user = getattr(http_request.state, "user", None)
    
    try:
        env = get_env()
        schema = env.get_schema()

        # Plan
        planner = Planner()
        steps = planner.plan(request.question)

        # Generate SQL
        sql_generator = SQLGenerator(schema)
        sql_queries = sql_generator.generate(request.question, request.context)

        # Execute queries
        execution_results: List[dict] = []
        for sql_query in sql_queries:
            try:
                results = env.execute_query(sql_query)
                execution_results.append({"query": sql_query.query, "results": results})
            except Exception as e:
                execution_results.append({"query": sql_query.query, "error": str(e)})

        # Generate response
        response = AgentResponse(
            answer=f"Based on the query results, here is the answer to: {request.question}",
            sql_queries=sql_queries,
            confidence=0.85,
            reasoning="Generated from SQL query results",
        )

        return QueryResponse(
            answer=response.answer,
            sql_queries=[q.query for q in response.sql_queries],
            confidence=response.confidence,
            reasoning=response.reasoning,
            execution_results=execution_results,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

