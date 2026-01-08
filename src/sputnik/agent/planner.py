"""Planning module for breaking down business questions into steps."""

import asyncio
import os
from typing import List, Optional

from sputnik.llm.client import create_llm_client
from sputnik.types import AgentResponse, SQLQuery


class Planner:
    """Plans the execution strategy for a business question."""

    def __init__(self, llm_client=None) -> None:
        """
        Initialize the planner.

        Args:
            llm_client: Optional LLM client (will create one if not provided)
        """
        self.llm_client = llm_client
        self._use_llm = os.getenv("USE_LLM_PLANNING", "true").lower() == "true"

    async def plan_async(self, query: str) -> List[str]:
        """
        Break down a business question into execution steps (async).

        Args:
            query: Natural language business question

        Returns:
            List of step descriptions
        """
        if not self._use_llm:
            return self._plan_fallback(query)

        try:
            if self.llm_client is None:
                self.llm_client = create_llm_client()

            system_prompt = """You are an expert data analyst planning SQL queries for ERP systems.
Break down business questions into clear, sequential execution steps.
Return only a JSON array of step descriptions, one per line, no additional text.

Example:
["Identify relevant tables", "Query revenue data", "Aggregate results"]"""

            prompt = f"""Break down this business question into execution steps:

Question: {query}

Return a JSON array of step descriptions:"""

            response = await self.llm_client.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.3,
                max_tokens=200,
            )

            # Try to parse JSON array from response
            import json
            import re

            # Extract JSON array from response
            json_match = re.search(r'\[.*?\]', response, re.DOTALL)
            if json_match:
                steps = json.loads(json_match.group())
                if isinstance(steps, list) and all(isinstance(s, str) for s in steps):
                    return steps

            # Fallback: split by lines and clean
            lines = [line.strip() for line in response.split("\n") if line.strip()]
            # Remove markdown formatting
            cleaned = [
                line.lstrip("- ").lstrip("* ").strip('"').strip("'")
                for line in lines
                if line and not line.startswith("[") and not line.startswith("]")
            ]
            return cleaned if cleaned else self._plan_fallback(query)

        except Exception as e:
            # Fallback to rule-based planning on error
            print(f"LLM planning failed: {e}, using fallback")
            return self._plan_fallback(query)

    def plan(self, query: str) -> List[str]:
        """
        Break down a business question into execution steps (sync wrapper).

        Args:
            query: Natural language business question

        Returns:
            List of step descriptions
        """
        if not self._use_llm:
            return self._plan_fallback(query)

        try:
            # Try to use existing event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, we need to use a different approach
                # For now, fallback to sync
                return self._plan_fallback(query)
            return loop.run_until_complete(self.plan_async(query))
        except RuntimeError:
            # No event loop, create one
            return asyncio.run(self.plan_async(query))

    def _plan_fallback(self, query: str) -> List[str]:
        """Fallback rule-based planning."""
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

