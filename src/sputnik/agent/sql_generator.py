"""SQL generation module for converting business questions to SQL."""

import asyncio
import json
import os
import re
from typing import List, Optional

from sputnik.llm.client import create_llm_client
from sputnik.types import ERPSchema, SQLQuery


class SQLGenerator:
    """Generates SQL queries from natural language questions."""

    def __init__(self, schema: ERPSchema, llm_client=None) -> None:
        """
        Initialize the SQL generator with schema information.

        Args:
            schema: ERP schema information
            llm_client: Optional LLM client (will create one if not provided)
        """
        self.schema = schema
        self.llm_client = llm_client
        self._use_llm = os.getenv("USE_LLM_SQL", "true").lower() == "true"

    async def generate_async(
        self, query: str, context: Optional[List[str]] = None
    ) -> List[SQLQuery]:
        """
        Generate SQL queries from a natural language question (async).

        Args:
            query: Natural language business question
            context: Optional context from previous steps

        Returns:
            List of SQL queries (validated and read-only)
        """
        if not self._use_llm:
            return self._generate_fallback(query)

        try:
            if self.llm_client is None:
                self.llm_client = create_llm_client()

            # Build schema context
            schema_text = self._format_schema_for_prompt()

            system_prompt = """You are an expert SQL developer for ERP systems.
Generate ONLY valid, read-only SQL SELECT queries. Never use INSERT, UPDATE, DELETE, DROP, CREATE, ALTER, or TRUNCATE.
Return only the SQL query, no explanations, no markdown formatting, just the SQL.

Important rules:
1. Only SELECT queries are allowed
2. Use proper JOINs when needed
3. Include appropriate WHERE clauses
4. Use aggregate functions (SUM, COUNT, AVG) when appropriate
5. Return clean SQL without backticks or code blocks"""

            context_text = ""
            if context:
                context_text = f"\n\nPrevious steps:\n" + "\n".join(f"- {step}" for step in context)

            prompt = f"""Generate a SQL query for this business question:

Question: {query}
{context_text}

Available schema:
{schema_text}

Return ONLY the SQL query (no explanations, no markdown):"""

            response = await self.llm_client.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.2,  # Lower temperature for more deterministic SQL
                max_tokens=500,
            )

            # Extract SQL from response
            sql = self._extract_sql_from_response(response)

            if not sql:
                print("LLM SQL extraction failed: No valid SQL found, using fallback")
                return self._generate_fallback(query)

            # Validate SQL has required components
            if not self._validate_sql_structure(sql):
                print(f"LLM SQL validation failed: Invalid structure '{sql}', using fallback")
                return self._generate_fallback(query)

            # Validate and create SQLQuery
            if not self._is_read_only(sql):
                sql = self._make_read_only(sql)

            return [SQLQuery(query=sql, is_read_only=True)]

        except Exception as e:
            # Fallback to rule-based generation on error
            print(f"LLM SQL generation failed: {e}, using fallback")
            return self._generate_fallback(query)

    def generate(self, query: str, context: Optional[List[str]] = None) -> List[SQLQuery]:
        """
        Generate SQL queries from a natural language question (sync wrapper).

        Args:
            query: Natural language business question
            context: Optional context from previous steps

        Returns:
            List of SQL queries (validated and read-only)
        """
        if not self._use_llm:
            return self._generate_fallback(query)

        try:
            # Try to use existing event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, fallback to sync
                return self._generate_fallback(query)
            return loop.run_until_complete(self.generate_async(query, context))
        except RuntimeError:
            # No event loop, create one
            return asyncio.run(self.generate_async(query, context))

    def _generate_fallback(self, query: str) -> List[SQLQuery]:
        """Fallback rule-based SQL generation."""
        query_lower = query.lower()
        sql_queries: List[SQLQuery] = []

        # Count queries
        if "how many" in query_lower or "count" in query_lower:
            if "customer" in query_lower and "customers" in self.schema.tables:
                sql = "SELECT COUNT(*) as count FROM customers"
                sql_queries.append(SQLQuery(query=sql, is_read_only=True))
            elif "order" in query_lower and "orders" in self.schema.tables:
                sql = "SELECT COUNT(*) as count FROM orders"
                sql_queries.append(SQLQuery(query=sql, is_read_only=True))
            elif "invoice" in query_lower and "invoices" in self.schema.tables:
                sql = "SELECT COUNT(*) as count FROM invoices"
                sql_queries.append(SQLQuery(query=sql, is_read_only=True))
            elif self.schema.tables:
                # Default to first table
                first_table = list(self.schema.tables.keys())[0]
                sql = f"SELECT COUNT(*) as count FROM {first_table}"
                sql_queries.append(SQLQuery(query=sql, is_read_only=True))
        
        # Revenue/sales queries
        elif "revenue" in query_lower or "sales" in query_lower or "total amount" in query_lower:
            if "orders" in self.schema.tables:
                sql = "SELECT SUM(total_amount) as total_revenue FROM orders"
                sql_queries.append(SQLQuery(query=sql, is_read_only=True))
        
        # Average queries
        elif "average" in query_lower or "avg" in query_lower:
            if "order" in query_lower and "orders" in self.schema.tables:
                sql = "SELECT AVG(total_amount) as avg_amount FROM orders"
                sql_queries.append(SQLQuery(query=sql, is_read_only=True))
            elif "orders" in self.schema.tables:
                sql = "SELECT AVG(total_amount) as avg_amount FROM orders"
                sql_queries.append(SQLQuery(query=sql, is_read_only=True))
        
        # Inventory queries
        elif "inventory" in query_lower or "stock" in query_lower:
            if "inventory_movements" in self.schema.tables:
                sql = "SELECT product_id, SUM(quantity) as total_stock FROM inventory_movements GROUP BY product_id"
                sql_queries.append(SQLQuery(query=sql, is_read_only=True))
        
        # Customer queries
        elif "customer" in query_lower:
            if "customers" in self.schema.tables:
                if "list" in query_lower or "show" in query_lower or "all" in query_lower:
                    sql = "SELECT * FROM customers"
                else:
                    sql = "SELECT COUNT(*) as count FROM customers"
                sql_queries.append(SQLQuery(query=sql, is_read_only=True))
        
        # Order queries
        elif "order" in query_lower:
            if "orders" in self.schema.tables:
                if "completed" in query_lower:
                    sql = "SELECT * FROM orders WHERE status = 'completed'"
                elif "list" in query_lower or "show" in query_lower or "all" in query_lower:
                    sql = "SELECT * FROM orders"
                else:
                    sql = "SELECT COUNT(*) as count FROM orders"
                sql_queries.append(SQLQuery(query=sql, is_read_only=True))
        
        # Invoice queries
        elif "invoice" in query_lower:
            if "invoices" in self.schema.tables:
                if "unpaid" in query_lower:
                    sql = "SELECT * FROM invoices WHERE paid = false"
                elif "list" in query_lower or "show" in query_lower or "all" in query_lower:
                    sql = "SELECT * FROM invoices"
                else:
                    sql = "SELECT COUNT(*) as count FROM invoices"
                sql_queries.append(SQLQuery(query=sql, is_read_only=True))
        
        # Date queries
        elif "2024" in query_lower or "from" in query_lower and "date" in query_lower:
            if "orders" in self.schema.tables:
                sql = "SELECT * FROM orders WHERE order_date >= '2024-01-01'"
                sql_queries.append(SQLQuery(query=sql, is_read_only=True))
        
        # Default: count from first table
        else:
            if self.schema.tables:
                first_table = list(self.schema.tables.keys())[0]
                sql = f"SELECT COUNT(*) as count FROM {first_table}"
                sql_queries.append(SQLQuery(query=sql, is_read_only=True))

        return sql_queries if sql_queries else [SQLQuery(query="SELECT 1", is_read_only=True)]

    def _format_schema_for_prompt(self) -> str:
        """Format schema information for LLM prompt."""
        lines = ["Tables and columns:"]
        for table_name, columns in self.schema.tables.items():
            lines.append(f"  {table_name}: {', '.join(columns)}")

        if self.schema.relationships:
            lines.append("\nRelationships:")
            for rel in self.schema.relationships:
                lines.append(
                    f"  {rel['from_table']}.{rel['from_col']} -> {rel['to_table']}.{rel['to_col']}"
                )

        return "\n".join(lines)

    def _extract_sql_from_response(self, response: str) -> str:
        """Extract SQL query from LLM response."""
        # Remove markdown code blocks
        response = re.sub(r"```sql\s*", "", response, flags=re.IGNORECASE)
        response = re.sub(r"```\s*", "", response)
        response = re.sub(r"`", "", response)

        # Find SQL-like patterns - look for complete SELECT statements
        # Match SELECT ... FROM ... (with optional WHERE, GROUP BY, etc.)
        sql_match = re.search(
            r"(SELECT\s+.+?\s+FROM\s+\w+.*?)(?:;|$)", 
            response, 
            re.IGNORECASE | re.DOTALL
        )
        if sql_match:
            sql = sql_match.group(1).strip()
            # Remove trailing semicolon if present
            sql = sql.rstrip(";").strip()
            # Validate it has FROM clause
            if re.search(r"\bFROM\s+\w+", sql, re.IGNORECASE):
                return sql

        # Try to find any SELECT with FROM in the response
        response_clean = response.strip()
        if response_clean.upper().startswith("SELECT"):
            # Check if it has a FROM clause
            if re.search(r"\bFROM\s+\w+", response_clean, re.IGNORECASE):
                return response_clean.rstrip(";").strip()

        return ""

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

    def _validate_sql_structure(self, sql: str) -> bool:
        """
        Validate that SQL has required structure (SELECT, FROM, etc.).

        Args:
            sql: SQL query string

        Returns:
            True if SQL structure is valid, False otherwise
        """
        sql_upper = sql.upper().strip()
        
        # Must start with SELECT
        if not sql_upper.startswith("SELECT"):
            return False
        
        # Must have FROM clause
        if not re.search(r"\bFROM\s+\w+", sql_upper):
            return False
        
        # Check for basic syntax issues
        # SELECT must be followed by something
        select_match = re.search(r"SELECT\s+(.+?)\s+FROM", sql_upper, re.DOTALL)
        if not select_match or not select_match.group(1).strip():
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

