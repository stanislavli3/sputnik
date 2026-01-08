"""Schema endpoints."""

from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from sputnik.env.duckdb_env import DuckDBEnv

router = APIRouter()

# Global environment (in production, use dependency injection)
_env: Optional[DuckDBEnv] = None


def get_env() -> DuckDBEnv:
    """Get or create the DuckDB environment."""
    global _env
    if _env is None:
        _env = DuckDBEnv("demo_erp.duckdb")
    return _env


class SchemaResponse(BaseModel):
    """Schema response model."""

    tables: dict
    relationships: List[dict]


@router.get("/schema", response_model=SchemaResponse)
async def get_schema() -> SchemaResponse:
    """
    Get the ERP schema.

    Returns:
        Schema information with tables and relationships
    """
    try:
        env = get_env()
        schema = env.get_schema()

        return SchemaResponse(
            tables={table: columns for table, columns in schema.tables.items()},
            relationships=schema.relationships,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

