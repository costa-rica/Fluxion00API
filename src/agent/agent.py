"""
Core Agent implementation for Fluxion00API.

This module provides the main Agent class that orchestrates LLM interactions
and tool execution to answer user questions.
"""

import json
import re
from typing import List, Dict, Any, Optional
from src.llm import BaseLLMProvider, LLMMessage
from src.utils import logger, truncate_text
from .tools import ToolRegistry, get_tool_registry
from .tools_articles import register_article_tools, format_articles_list
from .tools_sql import register_sql_tools


class Agent:
    """
    Main agent class that orchestrates LLM and tool interactions.

    The agent uses an LLM to understand user queries, determines which tools
    to use, executes them, and generates responses based on the results.
    """

    def __init__(
        self,
        llm_provider: BaseLLMProvider,
        tool_registry: Optional[ToolRegistry] = None,
        system_prompt: Optional[str] = None
    ):
        """
        Initialize the agent.

        Args:
            llm_provider: LLM provider instance
            tool_registry: Tool registry (uses global if not provided)
            system_prompt: Custom system prompt (uses default if not provided)
        """
        self.llm = llm_provider
        self.registry = tool_registry or get_tool_registry()
        self.conversation_history: List[LLMMessage] = []

        # Register article tools if not already registered
        if not self.registry.list_tools():
            register_article_tools(self.registry)
            register_sql_tools(self.registry)

        self.system_prompt = system_prompt or self._default_system_prompt()

    def _default_system_prompt(self) -> str:
        """
        Generate the default system prompt with tool descriptions.

        Returns:
            str: System prompt
        """
        tools_desc = self.registry.get_tools_description()

        return f"""You are a helpful AI assistant with access to a database of approved news articles.

You have access to the following tools to query the ArticleApproveds database:

{tools_desc}

When a user asks a question that requires querying the database, you should:

1. Determine which tool(s) would help answer the question
2. Respond with a tool call in this EXACT format:
   TOOL_CALL: tool_name
   ARGUMENTS:
   {{
     "param1": "value1",
     "param2": value2
   }}
   END_TOOL_CALL

3. After receiving tool results, use them to answer the user's question in a helpful way

If the user's question doesn't require database queries, answer directly.

Be concise, accurate, and helpful. When presenting article results, format them clearly.
"""

    def _parse_tool_call(self, response: str) -> Optional[Dict[str, Any]]:
        """
        Parse a tool call from the LLM response.

        Args:
            response: LLM response text

        Returns:
            Optional[Dict[str, Any]]: Parsed tool call or None
        """
        # Look for TOOL_CALL pattern
        tool_pattern = r"TOOL_CALL:\s*(\w+)\s*ARGUMENTS:\s*({.*?})\s*END_TOOL_CALL"
        match = re.search(tool_pattern, response, re.DOTALL)

        if match:
            tool_name = match.group(1).strip()
            try:
                arguments = json.loads(match.group(2))
                return {
                    "tool_name": tool_name,
                    "arguments": arguments
                }
            except json.JSONDecodeError:
                return None

        return None

    async def process_sql_query(
        self,
        user_question: str,
        progress_callback: Optional[callable] = None
    ) -> str:
        """
        Process a user question directly using Text-to-SQL tool.

        This bypasses the normal tool selection and directly invokes the
        execute_custom_sql tool, forcing SQL generation for the query.

        Args:
            user_question: User's natural language question
            progress_callback: Optional async callback(stage, message, details) for progress updates

        Returns:
            str: Agent's response with SQL results

        Example:
            >>> agent = Agent(llm_provider)
            >>> response = await agent.process_sql_query("Show articles from California")
        """
        # Add user message to history
        self.conversation_history.append(
            LLMMessage(role="user", content=user_question)
        )

        try:
            # Send progress: Generating SQL
            if progress_callback:
                await progress_callback(
                    "sql_generation",
                    "Generating SQL query from your question...",
                    {"question": truncate_text(user_question)}
                )

            # Directly execute SQL tool with agent's LLM provider
            logger.info(f"[TOOL] Executing: execute_custom_sql (forced)")
            logger.info(f"[TOOL] Question: {truncate_text(user_question)}")

            # Call SQL tool function directly to pass llm_provider
            from .tools_sql import execute_custom_sql_query
            tool_result = await execute_custom_sql_query(
                question=user_question,
                llm_provider=self.llm  # Pass agent's LLM provider
            )

            # Log tool result
            if tool_result["success"]:
                result_data = str(tool_result.get("data", ""))
                logger.info(f"[TOOL] Success | Output length: {len(result_data)} chars")

                # Send progress: SQL executed successfully
                if progress_callback:
                    row_count = tool_result.get('row_count', 'unknown')
                    await progress_callback(
                        "sql_executed",
                        f"SQL query executed successfully. Found {row_count} result(s).",
                        {"sql": tool_result.get("sql", ""), "row_count": row_count}
                    )
            else:
                logger.info(f"[TOOL] Failed | Error: {tool_result.get('error', 'Unknown error')}")

                # Send progress: SQL execution failed
                if progress_callback:
                    await progress_callback(
                        "sql_error",
                        f"SQL execution failed: {tool_result.get('error', 'Unknown error')}",
                        {"error": tool_result.get("error")}
                    )

            # Format SQL results
            from .tools_sql import format_sql_results
            formatted_data = format_sql_results(tool_result)

            # Send progress: Generating natural language response
            if progress_callback:
                await progress_callback(
                    "llm_summarizing",
                    "Generating natural language summary of results..."
                )

            # Send formatted results to LLM for natural language response
            messages = [
                LLMMessage(role="system", content=self.system_prompt),
                *self.conversation_history,
                LLMMessage(
                    role="user",
                    content=f"SQL query results:\n\n{formatted_data}\n\nPlease provide a clear, natural language summary of these results for the user."
                )
            ]

            final_response = await self.llm.chat(messages, temperature=0.3)
            response_text = final_response.content

            # Add assistant response to history
            self.conversation_history.append(
                LLMMessage(role="assistant", content=response_text)
            )

            return response_text

        except Exception as e:
            error_msg = f"Error executing SQL query: {str(e)}"
            logger.error(f"[TOOL] {error_msg}")

            # Add error to history
            self.conversation_history.append(
                LLMMessage(role="assistant", content=error_msg)
            )

            return error_msg

    async def process_message(
        self,
        user_message: str,
        progress_callback: Optional[callable] = None
    ) -> str:
        """
        Process a user message and generate a response.

        This is the main entry point for agent interactions.

        Args:
            user_message: User's message
            progress_callback: Optional async callback(stage, message, details) for progress updates

        Returns:
            str: Agent's response

        Example:
            >>> agent = Agent(llm_provider)
            >>> response = await agent.process_message("How many articles are approved?")
        """
        # Add user message to history
        self.conversation_history.append(
            LLMMessage(role="user", content=user_message)
        )

        # Send progress: Analyzing question
        if progress_callback:
            await progress_callback(
                "analyzing",
                "Analyzing your question...",
                {"message": truncate_text(user_message)}
            )

        # Get initial LLM response
        messages = [
            LLMMessage(role="system", content=self.system_prompt),
            *self.conversation_history
        ]

        llm_response = await self.llm.chat(messages, temperature=0.3)
        response_text = llm_response.content

        # Check if LLM wants to call a tool
        tool_call = self._parse_tool_call(response_text)

        if tool_call:
            # Log tool execution
            args_preview = truncate_text(json.dumps(tool_call["arguments"]))
            logger.info(f"[TOOL] Executing: {tool_call['tool_name']}")
            logger.info(f"[TOOL] Arguments: {args_preview}")

            # Send progress: Tool execution started
            if progress_callback:
                await progress_callback(
                    "tool_execution",
                    f"Executing tool: {tool_call['tool_name']}",
                    {"tool": tool_call['tool_name'], "arguments": tool_call["arguments"]}
                )

            # Execute the tool
            # Special handling for SQL tool to pass LLM provider
            if tool_call["tool_name"] == "execute_custom_sql":
                from .tools_sql import execute_custom_sql_query
                tool_result = await execute_custom_sql_query(
                    llm_provider=self.llm,  # Pass agent's LLM provider
                    **tool_call["arguments"]
                )
            else:
                tool_result = await self.registry.execute_tool(
                    tool_call["tool_name"],
                    **tool_call["arguments"]
                )

            # Log tool result
            if tool_result["success"]:
                # Calculate output length based on result type
                result_data = str(tool_result.get("data", ""))
                logger.info(f"[TOOL] Success | Output length: {len(result_data)} chars | Preview: \"{truncate_text(result_data)}\"")

                # Send progress: Tool execution succeeded
                if progress_callback:
                    await progress_callback(
                        "tool_success",
                        f"Tool '{tool_call['tool_name']}' executed successfully",
                        {"tool": tool_call['tool_name'], "output_length": len(result_data)}
                    )
            else:
                logger.info(f"[TOOL] Failed | Error: {tool_result.get('error', 'Unknown error')}")

                # Send progress: Tool execution failed
                if progress_callback:
                    await progress_callback(
                        "tool_error",
                        f"Tool '{tool_call['tool_name']}' failed: {tool_result.get('error', 'Unknown error')}",
                        {"tool": tool_call['tool_name'], "error": tool_result.get("error")}
                    )

            # Format tool result for LLM
            if tool_result["success"]:
                # Special formatting for SQL tool results
                if tool_call["tool_name"] == "execute_custom_sql":
                    from .tools_sql import format_sql_results
                    formatted_data = format_sql_results(tool_result)
                    tool_result_message = f"Tool '{tool_call['tool_name']}' executed successfully.\n\n{formatted_data}"
                else:
                    data = tool_result["data"]

                    # Special formatting for article lists
                    if isinstance(data, list) and data and isinstance(data[0], dict):
                        if "headlineForPdfReport" in data[0]:
                            formatted_data = format_articles_list(data)
                        else:
                            formatted_data = json.dumps(data, indent=2)
                    elif isinstance(data, dict) and "headlineForPdfReport" in data:
                        from .tools_articles import format_article_for_display
                        formatted_data = format_article_for_display(data)
                    else:
                        formatted_data = str(data)

                    tool_result_message = f"Tool '{tool_call['tool_name']}' executed successfully.\n\nResult:\n{formatted_data}"
            else:
                tool_result_message = f"Tool '{tool_call['tool_name']}' failed: {tool_result['error']}"

            # Send tool result back to LLM for final response
            messages.append(
                LLMMessage(role="assistant", content=response_text)
            )
            messages.append(
                LLMMessage(role="user", content=tool_result_message)
            )

            # Send progress: Generating final response
            if progress_callback:
                await progress_callback(
                    "generating_response",
                    "Generating final response..."
                )

            final_response = await self.llm.chat(messages, temperature=0.3)
            response_text = final_response.content

        # Add assistant response to history
        self.conversation_history.append(
            LLMMessage(role="assistant", content=response_text)
        )

        return response_text

    async def stream_response(self, user_message: str):
        """
        Process a user message and stream the response.

        Args:
            user_message: User's message

        Yields:
            str: Chunks of the agent's response

        Example:
            >>> async for chunk in agent.stream_response("Tell me about articles"):
            ...     print(chunk, end="", flush=True)
        """
        # Add user message to history
        self.conversation_history.append(
            LLMMessage(role="user", content=user_message)
        )

        # For streaming, we'll use a simpler approach without tool calls
        # (Tool calls don't work well with streaming)
        messages = [
            LLMMessage(role="system", content=self.system_prompt),
            *self.conversation_history
        ]

        full_response = ""
        async for chunk in self.llm.stream_generate(
            prompt=user_message,
            system_prompt=self.system_prompt,
            temperature=0.3
        ):
            full_response += chunk
            yield chunk

        # Add complete response to history
        self.conversation_history.append(
            LLMMessage(role="assistant", content=full_response)
        )

    def clear_history(self) -> None:
        """Clear the conversation history."""
        self.conversation_history = []

    def get_history(self) -> List[LLMMessage]:
        """
        Get the conversation history.

        Returns:
            List[LLMMessage]: Conversation history
        """
        return self.conversation_history.copy()

    def get_available_tools(self) -> List[str]:
        """
        Get list of available tool names.

        Returns:
            List[str]: Tool names
        """
        return [tool.name for tool in self.registry.list_tools()]


# Factory function for easy agent creation
def create_agent(
    llm_provider: BaseLLMProvider,
    include_article_tools: bool = True,
    include_sql_tools: bool = True
) -> Agent:
    """
    Factory function to create an agent instance.

    Args:
        llm_provider: LLM provider instance
        include_article_tools: Whether to register article tools
        include_sql_tools: Whether to register Text-to-SQL fallback tool

    Returns:
        Agent: Configured agent instance
    """
    registry = ToolRegistry()

    if include_article_tools:
        register_article_tools(registry)

    if include_sql_tools:
        register_sql_tools(registry)

    return Agent(llm_provider=llm_provider, tool_registry=registry)
