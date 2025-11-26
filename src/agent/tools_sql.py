"""
Text-to-SQL tool for the Fluxion00API agent.

This module provides a fallback tool that allows the LLM to generate
and execute custom SQL queries when pre-defined tools are insufficient.
"""

import re
import sqlite3
from pathlib import Path
from typing import Dict, Any, Optional
from src.database.readonly_connection import get_readonly_db
from .sql_security import validate_sql_security, enforce_result_limit, SQLSecurityError
from .tools import ToolRegistry, ToolParameter


# Path to SQL schema file
PROJECT_ROOT = Path(__file__).parent.parent.parent
SQL_SCHEMA_PATH = PROJECT_ROOT / 'docs' / 'SQL_SCHEMA.md'


def load_sql_schema() -> str:
    """
    Load the SQL schema reference for Text-to-SQL operations.

    Returns:
        str: SQL schema markdown content

    Raises:
        FileNotFoundError: If SQL_SCHEMA.md doesn't exist
    """
    if not SQL_SCHEMA_PATH.exists():
        raise FileNotFoundError(
            f"SQL_SCHEMA.md not found at {SQL_SCHEMA_PATH}. "
            "This file is required for Text-to-SQL functionality."
        )

    return SQL_SCHEMA_PATH.read_text()


def extract_sql_from_llm_response(response: str) -> Optional[str]:
    """
    Extract SQL query from LLM response.

    The LLM should return SQL in a code block or clearly marked format.

    Args:
        response: LLM response text

    Returns:
        Optional[str]: Extracted SQL query, or None if not found
    """
    # Try to find SQL in code blocks first
    # Pattern 1: ```sql ... ```
    sql_block_pattern = r'```(?:sql)?\s*(.*?)\s*```'
    match = re.search(sql_block_pattern, response, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # Pattern 2: Look for SELECT statement directly
    select_pattern = r'((?:WITH|SELECT)\s+.*?)(?:\n\n|$)'
    match = re.search(select_pattern, response, re.DOTALL | re.IGNORECASE)
    if match:
        sql = match.group(1).strip()
        # Clean up any trailing text
        sql = re.sub(r'[;]\s*$', '', sql)
        return sql

    return None


async def execute_custom_sql_query(question: str) -> Dict[str, Any]:
    """
    Generate and execute a custom SQL query based on natural language question.

    This is the main Text-to-SQL function that:
    1. Loads database schema
    2. Uses LLM to generate SQL
    3. Validates SQL for security
    4. Executes on read-only connection
    5. Returns results

    Args:
        question: Natural language question about the database

    Returns:
        Dict with:
            - success (bool): Whether query succeeded
            - data (list): Query results (if successful)
            - sql (str): Generated SQL query
            - error (str): Error message (if failed)
            - security_info (dict): Security validation details
    """
    from src.llm.ollama_client import get_ollama_provider

    try:
        # Load SQL schema
        try:
            schema = load_sql_schema()
        except FileNotFoundError as e:
            return {
                'success': False,
                'error': str(e),
                'reason': 'schema_not_found'
            }

        # Prepare prompt for LLM
        prompt = f"""You are a SQL expert. Given the following database schema and a user question, generate a SQL query to answer the question.

DATABASE SCHEMA:
{schema}

USER QUESTION: {question}

INSTRUCTIONS:
1. Generate a SELECT query only (no INSERT, UPDATE, DELETE, etc.)
2. Use proper SQLite syntax
3. Include appropriate WHERE clauses, JOINs, and aggregations as needed
4. Return ONLY the SQL query in a code block, no explanation
5. Ensure the query is efficient and answers the question directly

SQL QUERY:
"""

        # Get LLM response
        llm = get_ollama_provider()
        response = await llm.generate(
            prompt=prompt,
            temperature=0.1,  # Low temperature for precise SQL generation
            max_tokens=500
        )

        # Extract SQL from response
        sql = extract_sql_from_llm_response(response.content)

        if not sql:
            return {
                'success': False,
                'error': 'Could not extract SQL query from LLM response',
                'reason': 'sql_extraction_failed',
                'llm_response': response.content
            }

        # Validate SQL security
        security_result = validate_sql_security(sql)

        if not security_result['valid']:
            return {
                'success': False,
                'error': security_result['error'],
                'reason': security_result['reason'],
                'sql': sql,
                'security_info': security_result
            }

        # Execute query on read-only connection
        try:
            db = get_readonly_db()
            with db.get_cursor() as cursor:
                cursor.execute(sql)
                result_data = enforce_result_limit(cursor)

                return {
                    'success': True,
                    'sql': sql,
                    'data': result_data['data'],
                    'truncated': result_data.get('truncated', False),
                    'warning': result_data.get('warning'),
                    'security_info': security_result,
                    'row_count': len(result_data['data'])
                }

        except sqlite3.Error as e:
            return {
                'success': False,
                'error': f'Database error: {str(e)}',
                'reason': 'database_error',
                'sql': sql,
                'security_info': security_result
            }

    except Exception as e:
        return {
            'success': False,
            'error': f'Unexpected error: {str(e)}',
            'reason': 'unexpected_error'
        }


def format_sql_results(results: Dict[str, Any]) -> str:
    """
    Format SQL query results for display to the user.

    Args:
        results: Results dictionary from execute_custom_sql_query

    Returns:
        str: Formatted results string
    """
    if not results['success']:
        error_msg = f"Query failed: {results['error']}"
        if 'sql' in results:
            error_msg += f"\n\nGenerated SQL:\n```sql\n{results['sql']}\n```"
        return error_msg

    data = results['data']
    sql = results['sql']
    row_count = results.get('row_count', len(data))

    # Build formatted output
    output = f"Query executed successfully. Found {row_count} result(s).\n\n"

    if results.get('truncated'):
        output += f"⚠️ {results.get('warning', 'Results truncated')}\n\n"

    # Show generated SQL
    output += f"Generated SQL:\n```sql\n{sql}\n```\n\n"

    # Format results
    if not data:
        output += "No results found."
    elif len(data) == 1 and len(data[0]) == 1:
        # Single value result (e.g., COUNT)
        key = list(data[0].keys())[0]
        value = data[0][key]
        output += f"Result: {value}"
    else:
        # Table of results
        output += "Results:\n"
        for i, row in enumerate(data[:10], 1):  # Show first 10 rows
            output += f"\n--- Row {i} ---\n"
            for key, value in row.items():
                # Truncate long values
                if isinstance(value, str) and len(value) > 100:
                    value = value[:100] + "..."
                output += f"{key}: {value}\n"

        if len(data) > 10:
            output += f"\n... and {len(data) - 10} more row(s)"

    return output


def register_sql_tools(registry: ToolRegistry) -> None:
    """
    Register Text-to-SQL tool with the registry.

    Args:
        registry: Tool registry to register tools with
    """
    registry.register_function(
        name="execute_custom_sql",
        description=(
            "Generate and execute a custom SQL query to answer questions that "
            "cannot be answered by existing tools. Use this as a fallback when "
            "no other tool fits the user's question. The system will generate "
            "appropriate SQL based on the question and database schema."
        ),
        function=execute_custom_sql_query,
        parameters=[
            ToolParameter(
                name="question",
                type="string",
                description="Natural language question to answer using SQL query",
                required=True
            )
        ],
        category="database"
    )
