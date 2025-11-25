"""
Tool system for Fluxion00API agent.

This module provides a tool registry and execution system that allows
the agent to call functions and use their results to answer questions.
"""

from typing import Callable, Dict, Any, List, Optional
from dataclasses import dataclass, field
import json
import inspect


@dataclass
class ToolParameter:
    """Represents a parameter for a tool."""
    name: str
    type: str
    description: str
    required: bool = True
    default: Any = None


@dataclass
class Tool:
    """
    Represents a tool that the agent can use.

    A tool is a function that the agent can call to perform actions
    or retrieve information.
    """
    name: str
    description: str
    function: Callable
    parameters: List[ToolParameter] = field(default_factory=list)
    category: str = "general"

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert tool to dictionary format for LLM prompts.

        Returns:
            Dict[str, Any]: Tool description in dictionary format
        """
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "parameters": [
                {
                    "name": p.name,
                    "type": p.type,
                    "description": p.description,
                    "required": p.required,
                    "default": p.default
                }
                for p in self.parameters
            ]
        }

    def to_llm_description(self) -> str:
        """
        Format tool description for LLM prompt.

        Returns:
            str: Formatted tool description
        """
        params_desc = []
        for p in self.parameters:
            req = "required" if p.required else "optional"
            default = f", default={p.default}" if p.default is not None else ""
            params_desc.append(f"  - {p.name} ({p.type}, {req}{default}): {p.description}")

        params_str = "\n".join(params_desc) if params_desc else "  (no parameters)"

        return f"""
Tool: {self.name}
Category: {self.category}
Description: {self.description}
Parameters:
{params_str}
""".strip()

    async def execute(self, **kwargs) -> Any:
        """
        Execute the tool with given arguments.

        Args:
            **kwargs: Tool arguments

        Returns:
            Any: Tool execution result
        """
        # Filter kwargs to only include valid parameters
        valid_params = {p.name for p in self.parameters}
        filtered_kwargs = {k: v for k, v in kwargs.items() if k in valid_params}

        # Check if function is async
        if inspect.iscoroutinefunction(self.function):
            return await self.function(**filtered_kwargs)
        else:
            return self.function(**filtered_kwargs)


class ToolRegistry:
    """
    Registry for managing available tools.

    The tool registry maintains a collection of tools that the agent
    can use and provides methods to retrieve and execute them.
    """

    def __init__(self):
        """Initialize the tool registry."""
        self.tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """
        Register a tool.

        Args:
            tool: Tool to register
        """
        self.tools[tool.name] = tool

    def register_function(
        self,
        name: str,
        description: str,
        function: Callable,
        parameters: List[ToolParameter],
        category: str = "general"
    ) -> Tool:
        """
        Register a function as a tool.

        Args:
            name: Tool name
            description: Tool description
            function: Function to execute
            parameters: List of parameters
            category: Tool category

        Returns:
            Tool: The registered tool
        """
        tool = Tool(
            name=name,
            description=description,
            function=function,
            parameters=parameters,
            category=category
        )
        self.register(tool)
        return tool

    def get(self, name: str) -> Optional[Tool]:
        """
        Get a tool by name.

        Args:
            name: Tool name

        Returns:
            Optional[Tool]: The tool if found, None otherwise
        """
        return self.tools.get(name)

    def list_tools(self) -> List[Tool]:
        """
        Get list of all registered tools.

        Returns:
            List[Tool]: List of tools
        """
        return list(self.tools.values())

    def list_by_category(self, category: str) -> List[Tool]:
        """
        Get tools by category.

        Args:
            category: Category name

        Returns:
            List[Tool]: List of tools in category
        """
        return [tool for tool in self.tools.values() if tool.category == category]

    def get_tools_description(self) -> str:
        """
        Get formatted description of all tools for LLM prompt.

        Returns:
            str: Formatted tools description
        """
        if not self.tools:
            return "No tools available."

        descriptions = []
        for tool in self.tools.values():
            descriptions.append(tool.to_llm_description())

        return "\n\n".join(descriptions)

    async def execute_tool(self, name: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a tool by name.

        Args:
            name: Tool name
            **kwargs: Tool arguments

        Returns:
            Dict[str, Any]: Execution result with status and data
        """
        tool = self.get(name)

        if not tool:
            return {
                "success": False,
                "error": f"Tool '{name}' not found",
                "data": None
            }

        try:
            result = await tool.execute(**kwargs)
            return {
                "success": True,
                "error": None,
                "data": result,
                "tool_name": name
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "data": None,
                "tool_name": name
            }


# Global tool registry instance
_global_registry = ToolRegistry()


def get_tool_registry() -> ToolRegistry:
    """
    Get the global tool registry instance.

    Returns:
        ToolRegistry: The global tool registry
    """
    return _global_registry
