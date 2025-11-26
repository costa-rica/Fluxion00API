"""
SQL security validation for LLM-generated queries.

This module provides multiple layers of security validation to ensure
that LLM-generated SQL queries are safe to execute against the database.
"""

import re
from typing import Dict, Any, List, Optional


# Security Configuration
FORBIDDEN_SQL_KEYWORDS = [
    # Data modification
    'DELETE', 'INSERT', 'UPDATE', 'REPLACE', 'MERGE',

    # Schema modification
    'DROP', 'CREATE', 'ALTER', 'TRUNCATE', 'RENAME',

    # Transaction control
    'COMMIT', 'ROLLBACK', 'SAVEPOINT', 'BEGIN', 'TRANSACTION',

    # System commands
    'EXEC', 'EXECUTE', 'PRAGMA',

    # Database control
    'ATTACH', 'DETACH',

    # SQLite specific dangerous commands
    'VACUUM', 'REINDEX', 'ANALYZE',
]

# Maximum allowed result rows
MAX_RESULT_ROWS = 1000

# Maximum allowed query complexity (approximate token count)
MAX_QUERY_LENGTH = 2000


class SQLSecurityError(Exception):
    """Exception raised when SQL query fails security validation."""

    def __init__(self, message: str, reason: str):
        """
        Initialize security error.

        Args:
            message: Human-readable error message
            reason: Machine-readable reason code
        """
        super().__init__(message)
        self.reason = reason


def validate_keyword_blocklist(sql: str) -> Dict[str, Any]:
    """
    Check if SQL contains forbidden keywords.

    Args:
        sql: SQL query string

    Returns:
        Dict with 'valid' (bool) and optional 'error' (str), 'reason' (str)
    """
    # Normalize SQL for checking
    sql_upper = sql.upper()

    # Remove string literals to avoid false positives
    # (e.g., SELECT 'DELETE' should be allowed)
    sql_no_strings = re.sub(r"'[^']*'", '', sql_upper)
    sql_no_strings = re.sub(r'"[^"]*"', '', sql_no_strings)

    # Check for forbidden keywords
    for keyword in FORBIDDEN_SQL_KEYWORDS:
        # Use word boundaries to avoid false positives
        # (e.g., "DELETED_AT" column should be allowed)
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, sql_no_strings):
            return {
                'valid': False,
                'error': f'Query contains forbidden SQL keyword: {keyword}',
                'reason': 'keyword_blocklist',
                'blocked_keyword': keyword
            }

    return {'valid': True}


def validate_select_only(sql: str) -> Dict[str, Any]:
    """
    Validate that SQL is a SELECT statement only.

    Args:
        sql: SQL query string

    Returns:
        Dict with 'valid' (bool) and optional 'error' (str), 'reason' (str)
    """
    # Remove comments and normalize whitespace
    sql_clean = re.sub(r'--[^\n]*', '', sql)
    sql_clean = re.sub(r'/\*.*?\*/', '', sql_clean, flags=re.DOTALL)
    sql_clean = sql_clean.strip()

    # Check if query starts with SELECT or WITH (for CTEs)
    if not re.match(r'^\s*(SELECT|WITH)\s+', sql_clean, re.IGNORECASE):
        return {
            'valid': False,
            'error': 'Query must be a SELECT statement (or CTE starting with WITH)',
            'reason': 'not_select_statement'
        }

    return {'valid': True}


def validate_query_complexity(sql: str) -> Dict[str, Any]:
    """
    Validate that SQL query is not overly complex.

    Args:
        sql: SQL query string

    Returns:
        Dict with 'valid' (bool) and optional 'error' (str), 'reason' (str)
    """
    # Check query length
    if len(sql) > MAX_QUERY_LENGTH:
        return {
            'valid': False,
            'error': f'Query exceeds maximum length of {MAX_QUERY_LENGTH} characters',
            'reason': 'query_too_long'
        }

    # Count subqueries (as rough complexity measure)
    subquery_count = len(re.findall(r'\bSELECT\b', sql, re.IGNORECASE))
    if subquery_count > 5:
        return {
            'valid': False,
            'error': f'Query is too complex (contains {subquery_count} SELECT statements)',
            'reason': 'too_many_subqueries'
        }

    return {'valid': True}


def extract_table_names(sql: str) -> List[str]:
    """
    Extract table names from SQL query (best effort).

    Args:
        sql: SQL query string

    Returns:
        List of table names found in query
    """
    # Simple pattern matching for FROM and JOIN clauses
    pattern = r'\b(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)'
    matches = re.findall(pattern, sql, re.IGNORECASE)
    return list(set(matches))


def validate_sql_security(sql: str) -> Dict[str, Any]:
    """
    Run all security validations on SQL query.

    This is the main entry point for SQL security validation.
    Runs multiple validation layers and returns comprehensive results.

    Args:
        sql: SQL query string

    Returns:
        Dict with:
            - 'valid' (bool): Overall validation result
            - 'error' (str): Error message if validation failed
            - 'reason' (str): Machine-readable reason code
            - 'validations' (dict): Individual validation results
            - 'metadata' (dict): Query metadata (tables, etc.)
    """
    if not sql or not sql.strip():
        return {
            'valid': False,
            'error': 'SQL query is empty',
            'reason': 'empty_query'
        }

    validations = {}

    # Layer 1: Keyword blocklist
    keyword_result = validate_keyword_blocklist(sql)
    validations['keyword_blocklist'] = keyword_result
    if not keyword_result['valid']:
        return {
            'valid': False,
            'error': keyword_result['error'],
            'reason': keyword_result['reason'],
            'validations': validations,
            'blocked_keyword': keyword_result.get('blocked_keyword')
        }

    # Layer 2: SELECT-only validation
    select_result = validate_select_only(sql)
    validations['select_only'] = select_result
    if not select_result['valid']:
        return {
            'valid': False,
            'error': select_result['error'],
            'reason': select_result['reason'],
            'validations': validations
        }

    # Layer 3: Query complexity
    complexity_result = validate_query_complexity(sql)
    validations['complexity'] = complexity_result
    if not complexity_result['valid']:
        return {
            'valid': False,
            'error': complexity_result['error'],
            'reason': complexity_result['reason'],
            'validations': validations
        }

    # Extract metadata
    metadata = {
        'tables': extract_table_names(sql),
        'length': len(sql)
    }

    return {
        'valid': True,
        'validations': validations,
        'metadata': metadata
    }


def enforce_result_limit(cursor, max_rows: int = MAX_RESULT_ROWS) -> List[Dict[str, Any]]:
    """
    Fetch results with enforced row limit.

    Args:
        cursor: Database cursor after query execution
        max_rows: Maximum number of rows to fetch

    Returns:
        List of result rows as dictionaries
    """
    rows = cursor.fetchmany(max_rows + 1)

    if len(rows) > max_rows:
        # Truncate and warn
        return {
            'truncated': True,
            'max_rows': max_rows,
            'data': [dict(row) for row in rows[:max_rows]],
            'warning': f'Results truncated to {max_rows} rows'
        }

    return {
        'truncated': False,
        'data': [dict(row) for row in rows]
    }
