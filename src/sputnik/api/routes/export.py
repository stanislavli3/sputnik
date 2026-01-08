"""Query export endpoints."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse
import csv
import io
import json

from sputnik.api.db import get_history_db

router = APIRouter()


@router.get("/queries/{query_id}/export")
async def export_query(
    query_id: str,
    format: str = "csv",  # csv, json, or sql
) -> Response:
    """
    Export query results.

    Args:
        query_id: Query ID
        format: Export format (csv, json, sql)

    Returns:
        Exported data
    """
    try:
        history_db = get_history_db()
        query = history_db.get_query(query_id)
        
        if not query:
            raise HTTPException(status_code=404, detail="Query not found")
        
        # Parse execution_results if it's a string
        execution_results = query.get("execution_results")
        if isinstance(execution_results, str):
            try:
                execution_results = json.loads(execution_results)
            except:
                execution_results = None
        
        if format == "csv":
            return _export_csv(query, execution_results)
        elif format == "json":
            return _export_json(query, execution_results)
        elif format == "sql":
            return _export_sql(query)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _export_csv(query: dict, execution_results: Optional[list]) -> StreamingResponse:
    """Export query results as CSV."""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write metadata
    writer.writerow(["Query ID", query["id"]])
    writer.writerow(["Question", query["question"]])
    writer.writerow(["Answer", query.get("answer", "")])
    writer.writerow(["Confidence", f"{query.get('confidence', 0) * 100:.1f}%"])
    writer.writerow(["Created At", query.get("created_at", "")])
    writer.writerow([])
    
    # Write SQL queries
    writer.writerow(["SQL Queries"])
    for sql in query.get("sql_queries", []):
        writer.writerow([sql])
    writer.writerow([])
    
    # Write execution results
    if execution_results:
        writer.writerow(["Execution Results"])
        for i, result in enumerate(execution_results):
            writer.writerow([f"Query {i + 1}"])
            if result.get("error"):
                writer.writerow(["Error", result["error"]])
            elif result.get("results"):
                results = result["results"]
                if results and len(results) > 0:
                    # Write headers
                    if isinstance(results[0], dict):
                        writer.writerow(list(results[0].keys()))
                        # Write rows
                        for row in results:
                            writer.writerow(list(row.values()))
                    else:
                        writer.writerow(["Result"])
                        for row in results:
                            writer.writerow([row])
            writer.writerow([])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=query_{query['id']}.csv"}
    )


def _export_json(query: dict, execution_results: Optional[list]) -> Response:
    """Export query results as JSON."""
    export_data = {
        "query_id": query["id"],
        "question": query["question"],
        "answer": query.get("answer"),
        "confidence": query.get("confidence"),
        "sql_queries": query.get("sql_queries", []),
        "execution_results": execution_results,
        "created_at": query.get("created_at"),
        "execution_time_ms": query.get("execution_time_ms"),
    }
    
    return Response(
        content=json.dumps(export_data, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=query_{query['id']}.json"}
    )


def _export_sql(query: dict) -> Response:
    """Export SQL queries as text."""
    sql_queries = query.get("sql_queries", [])
    sql_text = "\n\n".join([f"-- Query {i + 1}\n{q}" for i, q in enumerate(sql_queries)])
    
    return Response(
        content=sql_text,
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename=query_{query['id']}.sql"}
    )
