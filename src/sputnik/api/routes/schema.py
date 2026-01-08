"""Schema endpoints."""

from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from sputnik.env.duckdb_env import DuckDBEnv
from sputnik.api.cache import get_schema_cache

router = APIRouter()
schema_cache = get_schema_cache()

# Global environment (in production, use dependency injection)
_env: Optional[DuckDBEnv] = None


def get_env() -> DuckDBEnv:
    """Get or create the DuckDB environment."""
    global _env
    if _env is None:
        _env = DuckDBEnv("demo_erp.duckdb")
    return _env


class TableStats(BaseModel):
    """Table statistics model."""

    row_count: int
    column_count: int
    size_bytes: Optional[int] = None
    last_updated: Optional[str] = None


class SchemaResponse(BaseModel):
    """Schema response model."""

    tables: dict
    relationships: List[dict]
    table_stats: Optional[Dict[str, TableStats]] = None


@router.get("/schema", response_model=SchemaResponse)
async def get_schema(include_stats: bool = False) -> SchemaResponse:
    """
    Get the ERP schema.

    Args:
        include_stats: Whether to include table statistics

    Returns:
        Schema information with tables and relationships
    """
    try:
        # Check cache (schema rarely changes)
        cache_key = f"schema_{include_stats}"
        cached = schema_cache.get(cache_key)
        if cached:
            return SchemaResponse(**cached)
        
        env = get_env()
        schema = env.get_schema()

        response_data = {
            "tables": {table: columns for table, columns in schema.tables.items()},
            "relationships": schema.relationships,
        }

        # Add table statistics if requested
        if include_stats:
            table_stats = {}
            for table_name in schema.tables.keys():
                try:
                    stats = _get_table_stats(env, table_name)
                    table_stats[table_name] = stats
                except Exception as e:
                    # If stats fail, just skip this table
                    print(f"Failed to get stats for {table_name}: {e}")
                    continue
            response_data["table_stats"] = table_stats

        # Cache result (5 minute TTL for schema)
        schema_cache.set(cache_key, response_data, ttl=300)
        
        return SchemaResponse(**response_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schema/tables/{table_name}/stats", response_model=TableStats)
async def get_table_stats(table_name: str) -> TableStats:
    """
    Get statistics for a specific table.

    Args:
        table_name: Name of the table

    Returns:
        Table statistics
    """
    try:
        env = get_env()
        stats = _get_table_stats(env, table_name)
        return TableStats(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _get_table_stats(env: DuckDBEnv, table_name: str) -> Dict[str, Any]:
    """Get statistics for a table."""
    conn = env.conn
    
    # Get row count
    try:
        row_count_result = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
        row_count = row_count_result[0] if row_count_result else 0
    except Exception:
        row_count = 0
    
    # Get column count from schema
    schema = env.get_schema()
    column_count = len(schema.tables.get(table_name, {}))
    
    # Get table size (DuckDB specific)
    size_bytes = None
    try:
        # DuckDB doesn't have a direct size query, but we can estimate
        # For now, we'll skip this or use a placeholder
        pass
    except Exception:
        pass
    
    return {
        "row_count": row_count,
        "column_count": column_count,
        "size_bytes": size_bytes,
        "last_updated": None,  # DuckDB doesn't track this
    }

