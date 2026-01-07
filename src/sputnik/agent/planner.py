"""Planning module for breaking down business questions into steps."""

from typing import List

from sputnik.types import AgentResponse, SQLQuery


class Planner:
    """Plans the execution strategy for a business question."""

    def __init__(self) -> None:
        """Initialize the planner."""
        pass

    def plan(self, query: str) -> List[str]:
        """
        Break down a business question into execution steps.

        Args:
            query: Natural language business question

        Returns:
            List of step descriptions
        """
        # Mock implementation: simple rule-based planning
        query_lower = query.lower()

        if "revenue" in query_lower or "sales" in query_lower:
            return ["Identify revenue tables", "Query revenue data", "Aggregate results"]
        elif "inventory" in query_lower or "stock" in query_lower:
            return ["Identify inventory tables", "Query inventory data", "Calculate metrics"]
        elif "customer" in query_lower:
            return ["Identify customer tables", "Query customer data", "Format results"]
        else:
            return ["Identify relevant tables", "Query data", "Format results"]

    def validate_response(self, response: AgentResponse) -> bool:
        """
        Validate that the agent response is complete and safe.

        Args:
            response: The agent response to validate

        Returns:
            True if valid, False otherwise
        """
        if not response.answer:
            return False

        # All SQL queries must be read-only
        if not all(q.is_read_only for q in response.sql_queries):
            return False

        return True

