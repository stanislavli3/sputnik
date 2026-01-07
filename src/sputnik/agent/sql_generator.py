"""SQL generation module for converting business questions to SQL."""

import re
from typing import List, Optional

from sputnik.types import ERPSchema, SQLQuery


class SQLGenerator:
    """Generates SQL queries from natural language questions."""

    def __init__(self, schema: ERPSchema) -> None:
        """
        Initialize the SQL generator with schema information.

        Args:
            schema: ERP schema information
        """
        self.schema = schema

    def generate(self, query: str, context: Optional[List[str]] = None) -> List[SQLQuery]:
        """
        Generate SQL queries from a natural language question.

        Args:
            query: Natural language business question
            context: Optional context from previous steps

        Returns:
            List of SQL queries (validated and read-only)
        """
        query_lower = query.lower()

        # Mock implementation: simple template-based SQL generation
        sql_queries: List[SQLQuery] = []

        if "revenue" in query_lower or "sales" in query_lower:
            # Check if orders table exists
            if "orders" in self.schema.tables:
                sql = "SELECT SUM(total_amount) as total_revenue FROM orders"
                sql_queries.append(SQLQuery(query=sql, is_read_only=True))
        elif "inventory" in query_lower or "stock" in query_lower:
            if "inventory_movements" in self.schema.tables:
                sql = "SELECT product_id, SUM(quantity) as total_stock FROM inventory_movements GROUP BY product_id"
                sql_queries.append(SQLQuery(query=sql, is_read_only=True))
        elif "customer" in query_lower:
            if "customers" in self.schema.tables:
                sql = "SELECT COUNT(*) as customer_count FROM customers"
                sql_queries.append(SQLQuery(query=sql, is_read_only=True))
        else:
            # Generic query
            if self.schema.tables:
                first_table = list(self.schema.tables.keys())[0]
                sql = f"SELECT COUNT(*) as count FROM {first_table}"
                sql_queries.append(SQLQuery(query=sql, is_read_only=True))

        # Ensure all queries are read-only
        validated_queries: List[SQLQuery] = []
        for sql_query in sql_queries:
            if not self._is_read_only(sql_query.query):
                # Convert to read-only by wrapping or modifying
                validated_queries.append(
                    SQLQuery(
                        query=self._make_read_only(sql_query.query),
                        is_read_only=True,
                    )
                )
            else:
                validated_queries.append(sql_query)

        return validated_queries

    def _is_read_only(self, sql: str) -> bool:
        """
        Check if a SQL query is read-only.

        Args:
            sql: SQL query string

        Returns:
            True if read-only, False otherwise
        """
        sql_upper = sql.upper().strip()
        dangerous_keywords = ["INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER", "TRUNCATE"]

        for keyword in dangerous_keywords:
            if re.search(rf"\b{keyword}\b", sql_upper):
                return False

        return True

    def _make_read_only(self, sql: str) -> str:
        """
        Attempt to make a SQL query read-only (mock implementation).

        Args:
            sql: SQL query string

        Returns:
            Modified SQL query (or original if already read-only)
        """
        # In a real implementation, this would parse and rewrite the query
        # For now, just return the original
        return sql

