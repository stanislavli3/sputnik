"""Tool routing module for executing agent tools."""

from typing import Any, Dict, List, Optional

from sputnik.types import ToolCall


class ToolRouter:
    """Routes and executes tool calls."""

    def __init__(self, available_tools: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the tool router.

        Args:
            available_tools: Dictionary of tool_name -> tool_function
        """
        self.tools: Dict[str, Any] = available_tools or {}

    def register_tool(self, name: str, tool_func: Any) -> None:
        """
        Register a tool with the router.

        Args:
            name: Tool name
            tool_func: Tool function
        """
        self.tools[name] = tool_func

    def execute(self, tool_call: ToolCall) -> Any:
        """
        Execute a tool call.

        Args:
            tool_call: The tool call to execute

        Returns:
            Tool execution result
        """
        if tool_call.tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_call.tool_name}' not found")

        tool_func = self.tools[tool_call.tool_name]
        return tool_func(**tool_call.arguments)

    def execute_batch(self, tool_calls: List[ToolCall]) -> List[Any]:
        """
        Execute multiple tool calls.

        Args:
            tool_calls: List of tool calls to execute

        Returns:
            List of execution results
        """
        return [self.execute(tc) for tc in tool_calls]

