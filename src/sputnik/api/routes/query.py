"""Query endpoints."""

import time
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from sputnik.agent.planner import Planner
from sputnik.agent.sql_generator import SQLGenerator
from sputnik.api.db import get_history_db
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
    model_id: Optional[str] = None  # Format: "provider:model" (e.g., "ollama:llama3")


class QueryResponse(BaseModel):
    """Query response model."""

    answer: str
    sql_queries: List[str]
    confidence: float
    reasoning: Optional[str] = None
    execution_results: Optional[List[dict]] = None
    query_id: Optional[str] = None  # ID of saved query in history


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
    user_id = user.get("id") if user else None
    
    # Track execution time
    start_time = time.time()
    
    try:
        env = get_env()
        schema = env.get_schema()

        # Create LLM client with selected model if provided
        llm_client = None
        if request.model_id:
            try:
                from sputnik.llm.client import create_llm_client
                parts = request.model_id.split(":", 1)
                if len(parts) == 2:
                    provider, model = parts
                    llm_client = create_llm_client(provider=provider, model=model)
            except Exception as e:
                print(f"Failed to create LLM client with model {request.model_id}: {e}")

        # Plan
        planner = Planner(llm_client=llm_client)
        steps = planner.plan(request.question)

        # Generate SQL
        sql_generator = SQLGenerator(schema, llm_client=llm_client)
        sql_queries = sql_generator.generate(request.question, request.context)

        # Execute queries
        execution_results: List[dict] = []
        for sql_query in sql_queries:
            try:
                results = env.execute_query(sql_query)
                execution_results.append({"query": sql_query.query, "results": results})
            except Exception as e:
                execution_results.append({"query": sql_query.query, "error": str(e)})

        # Generate answer from query results
        answer = ""
        reasoning = "Generated from SQL query results"
        confidence = 0.85  # Default confidence
        
        # Extract meaningful answer from results
        if execution_results and any("results" in r for r in execution_results):
            successful_results = [r for r in execution_results if "results" in r and not r.get("error")]
            
            if successful_results:
                # Try to use LLM for answer generation if available
                try:
                    # Use the same LLM client if available, otherwise create default
                    if not llm_client:
                        from sputnik.llm.client import create_llm_client
                        llm_client = create_llm_client()
                    
                    results_text = ""
                    for i, result in enumerate(successful_results):
                        if "results" in result:
                            results_text += f"\nQuery {i+1} results:\n"
                            # Format results nicely
                            query_results = result["results"][:5]  # First 5 rows
                            if query_results:
                                # Get column names from first row
                                if isinstance(query_results[0], dict):
                                    results_text += "  " + ", ".join(query_results[0].keys()) + "\n"
                                    for row in query_results:
                                        values = [str(v) for v in row.values()]
                                        results_text += "  " + ", ".join(values) + "\n"
                                else:
                                    results_text += str(query_results) + "\n"
                    
                    prompt = f"""Based on these SQL query results, provide a clear, concise answer to the business question.

Question: {request.question}

Query Results:
{results_text}

Provide a natural language answer:"""
                    
                    answer = await llm_client.generate(
                        prompt=prompt,
                        system_prompt="You are a data analyst explaining query results in business terms. Be concise and accurate.",
                        temperature=0.5,
                        max_tokens=300,
                    )
                    reasoning = "Generated using LLM from SQL query results"
                    confidence = 0.90  # Higher confidence when LLM generates answer
                except Exception as e:
                    print(f"LLM answer generation failed: {e}, using fallback")
                    # Fallback: Generate answer from results directly
                    answer = _generate_fallback_answer(request.question, successful_results)
                    confidence = 0.75  # Lower confidence for fallback
            else:
                # All queries failed
                answer = f"Unable to execute the query: {request.question}. Please check the query syntax or database connection."
                confidence = 0.10
        else:
            answer = f"No results returned for the query: {request.question}"
            confidence = 0.20

        # Generate response
        response = AgentResponse(
            answer=answer,
            sql_queries=sql_queries,
            confidence=confidence,
            reasoning=reasoning,
        )
        
        # Calculate execution time
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        query_response = QueryResponse(
            answer=response.answer,
            sql_queries=[q.query for q in response.sql_queries],
            confidence=response.confidence,
            reasoning=response.reasoning,
            execution_results=execution_results,
        )
        
        # Save to history (async, don't block response)
        query_id = None
        try:
            history_db = get_history_db()
            query_id = history_db.save_query(
                question=request.question,
                sql_queries=[q.query for q in sql_queries],
                answer=answer,
                confidence=confidence,
                execution_results=execution_results,
                execution_time_ms=execution_time_ms,
                model_id=request.model_id,
                user_id=user_id,
            )
            
            # Auto-create review if confidence is low or risk is high
            if confidence < 0.75:  # Low confidence threshold
                try:
                    from sputnik.api.db import get_reviews_db
                    reviews_db = get_reviews_db()
                    priority = "high" if confidence < 0.60 else "medium"
                    reviews_db.create_review(
                        query_id=query_id,
                        priority=priority,
                        submitted_by=user_id,
                    )
                except Exception as e:
                    print(f"Failed to create review: {e}")
        except Exception as e:
            # Log but don't fail the request
            print(f"Failed to save query history: {e}")
        
        # Add query_id to response
        query_response.query_id = query_id
        
        return query_response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _generate_fallback_answer(question: str, execution_results: List[dict]) -> str:
    """Generate a simple answer from query results without LLM."""
    if not execution_results:
        return f"Query executed but returned no results for: {question}"
    
    question_lower = question.lower()
    
    for result in execution_results:
        if "results" in result and result["results"]:
            query_results = result["results"]
            
            # Handle COUNT queries
            if len(query_results) == 1 and isinstance(query_results[0], dict):
                row = query_results[0]
                # Check for common count patterns
                if "count" in row:
                    count = row["count"]
                    # Check SQL query to determine what was counted
                    sql_query = result.get("query", "").upper()
                    
                    # Generic "info" queries - provide more context
                    if "info" in question_lower or "information" in question_lower or question_lower.strip() == "give info":
                        if "CUSTOMERS" in sql_query:
                            return f"Database Information: There are {count} customer(s) in the database."
                        elif "ORDERS" in sql_query:
                            return f"Database Information: There are {count} order(s) in the database."
                        elif "INVOICES" in sql_query:
                            return f"Database Information: There are {count} invoice(s) in the database."
                        else:
                            # Try to extract table name from SQL
                            return f"Database Information: The query found {count} record(s)."
                    
                    # Specific entity queries
                    if "customer" in question_lower:
                        return f"There are {count} customer(s) in the database."
                    elif "order" in question_lower:
                        return f"There are {count} order(s) in the database."
                    elif "invoice" in question_lower:
                        return f"There are {count} invoice(s) in the database."
                    else:
                        return f"The query returned a count of {count}."
                
                # Handle single value results
                if len(row) == 1:
                    key, value = next(iter(row.items()))
                    return f"The {key} is {value}."
                
                # Handle multiple columns - format as table summary
                if len(row) <= 3:
                    parts = [f"{k}: {v}" for k, v in row.items()]
                    return f"Result: {', '.join(parts)}"
            
            # Handle multiple rows
            if len(query_results) > 1:
                return f"Query returned {len(query_results)} result(s)."
            elif len(query_results) == 1:
                row = query_results[0]
                if isinstance(row, dict):
                    parts = [f"{k}: {v}" for k, v in row.items()]
                    return f"Result: {', '.join(parts)}"
                else:
                    return f"Result: {row}"
    
    return f"Query executed successfully for: {question}"

