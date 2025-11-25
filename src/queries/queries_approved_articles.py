"""
Query functions for the ArticleApproveds table.

This module provides functions to query the ArticleApproveds table
using raw SQL queries.
"""

from typing import List, Dict, Any, Optional
from datetime import date
from src.database.connection import get_db


def get_approved_articles_count(is_approved: bool = True) -> int:
    """
    Get the count of articles with a specific approval status.

    Args:
        is_approved: If True, count approved articles. If False, count non-approved.

    Returns:
        int: Count of articles matching the approval status

    Example:
        >>> count = get_approved_articles_count(is_approved=True)
        >>> print(f"Total approved articles: {count}")
    """
    db = get_db()

    query = """
        SELECT COUNT(*) as count
        FROM ArticleApproveds
        WHERE isApproved = ?
    """

    with db.get_cursor() as cursor:
        cursor.execute(query, (1 if is_approved else 0,))
        result = cursor.fetchone()
        return result['count'] if result else 0


def search_approved_articles_by_text(
    search_text: str,
    search_fields: Optional[List[str]] = None,
    is_approved: Optional[bool] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Search approved articles by text content across specified fields.

    Args:
        search_text: Text to search for
        search_fields: List of fields to search in. Options: 'headlineForPdfReport',
                      'kmNotes', 'textForPdfReport', 'publicationNameForPdfReport'.
                      If None, searches all fields.
        is_approved: Filter by approval status. If None, returns all statuses.
        limit: Maximum number of results to return (default: 100)

    Returns:
        List of dictionaries containing article data

    Example:
        >>> results = search_approved_articles_by_text("safety", is_approved=True)
    """
    db = get_db()

    # Default to searching all text fields
    if search_fields is None:
        search_fields = [
            'headlineForPdfReport',
            'kmNotes',
            'textForPdfReport',
            'publicationNameForPdfReport'
        ]

    # Build WHERE clause for text search
    text_conditions = []
    params = []

    for field in search_fields:
        text_conditions.append(f"{field} LIKE ?")
        params.append(f"%{search_text}%")

    where_clause = f"({' OR '.join(text_conditions)})"

    # Add approval status filter if specified
    if is_approved is not None:
        where_clause += " AND isApproved = ?"
        params.append(1 if is_approved else 0)

    query = f"""
        SELECT
            id,
            userId,
            articleId,
            isApproved,
            headlineForPdfReport,
            publicationNameForPdfReport,
            publicationDateForPdfReport,
            textForPdfReport,
            urlForPdfReport,
            kmNotes,
            createdAt,
            updatedAt
        FROM ArticleApproveds
        WHERE {where_clause}
        ORDER BY createdAt DESC
        LIMIT ?
    """

    params.append(limit)

    with db.get_cursor() as cursor:
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_approved_articles_by_user(
    user_id: int,
    is_approved: Optional[bool] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Get articles approved by a specific user.

    Args:
        user_id: ID of the user who approved the articles
        is_approved: Filter by approval status. If None, returns all statuses.
        limit: Maximum number of results to return (default: 100)

    Returns:
        List of dictionaries containing article data

    Example:
        >>> user_articles = get_approved_articles_by_user(user_id=1, is_approved=True)
    """
    db = get_db()

    where_clause = "userId = ?"
    params = [user_id]

    if is_approved is not None:
        where_clause += " AND isApproved = ?"
        params.append(1 if is_approved else 0)

    query = f"""
        SELECT
            id,
            userId,
            articleId,
            isApproved,
            headlineForPdfReport,
            publicationNameForPdfReport,
            publicationDateForPdfReport,
            textForPdfReport,
            urlForPdfReport,
            kmNotes,
            createdAt,
            updatedAt
        FROM ArticleApproveds
        WHERE {where_clause}
        ORDER BY createdAt DESC
        LIMIT ?
    """

    params.append(limit)

    with db.get_cursor() as cursor:
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_approved_articles_by_date_range(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    date_field: str = 'createdAt',
    is_approved: Optional[bool] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Get articles within a date range.

    Args:
        start_date: Start date in 'YYYY-MM-DD' format. If None, no lower bound.
        end_date: End date in 'YYYY-MM-DD' format. If None, no upper bound.
        date_field: Field to filter by ('createdAt', 'updatedAt', or 'publicationDateForPdfReport')
        is_approved: Filter by approval status. If None, returns all statuses.
        limit: Maximum number of results to return (default: 100)

    Returns:
        List of dictionaries containing article data

    Example:
        >>> articles = get_approved_articles_by_date_range(
        ...     start_date='2024-01-01',
        ...     end_date='2024-12-31',
        ...     is_approved=True
        ... )
    """
    db = get_db()

    # Validate date_field
    valid_date_fields = ['createdAt', 'updatedAt', 'publicationDateForPdfReport']
    if date_field not in valid_date_fields:
        raise ValueError(f"date_field must be one of {valid_date_fields}")

    conditions = []
    params = []

    if start_date:
        conditions.append(f"{date_field} >= ?")
        params.append(start_date)

    if end_date:
        conditions.append(f"{date_field} <= ?")
        params.append(end_date)

    if is_approved is not None:
        conditions.append("isApproved = ?")
        params.append(1 if is_approved else 0)

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    query = f"""
        SELECT
            id,
            userId,
            articleId,
            isApproved,
            headlineForPdfReport,
            publicationNameForPdfReport,
            publicationDateForPdfReport,
            textForPdfReport,
            urlForPdfReport,
            kmNotes,
            createdAt,
            updatedAt
        FROM ArticleApproveds
        WHERE {where_clause}
        ORDER BY {date_field} DESC
        LIMIT ?
    """

    params.append(limit)

    with db.get_cursor() as cursor:
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_approved_article_by_id(article_approved_id: int) -> Optional[Dict[str, Any]]:
    """
    Get a single approved article record by its ID.

    Args:
        article_approved_id: ID of the ArticleApproved record

    Returns:
        Dictionary containing article data, or None if not found

    Example:
        >>> article = get_approved_article_by_id(1)
    """
    db = get_db()

    query = """
        SELECT
            id,
            userId,
            articleId,
            isApproved,
            headlineForPdfReport,
            publicationNameForPdfReport,
            publicationDateForPdfReport,
            textForPdfReport,
            urlForPdfReport,
            kmNotes,
            createdAt,
            updatedAt
        FROM ArticleApproveds
        WHERE id = ?
    """

    with db.get_cursor() as cursor:
        cursor.execute(query, (article_approved_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_all_approved_articles(
    is_approved: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """
    Get all approved article records with pagination.

    Args:
        is_approved: Filter by approval status. If None, returns all statuses.
        limit: Maximum number of results to return (default: 100)
        offset: Number of records to skip (default: 0)

    Returns:
        List of dictionaries containing article data

    Example:
        >>> articles = get_all_approved_articles(is_approved=True, limit=50)
    """
    db = get_db()

    where_clause = "1=1"
    params = []

    if is_approved is not None:
        where_clause = "isApproved = ?"
        params.append(1 if is_approved else 0)

    query = f"""
        SELECT
            id,
            userId,
            articleId,
            isApproved,
            headlineForPdfReport,
            publicationNameForPdfReport,
            publicationDateForPdfReport,
            textForPdfReport,
            urlForPdfReport,
            kmNotes,
            createdAt,
            updatedAt
        FROM ArticleApproveds
        WHERE {where_clause}
        ORDER BY createdAt DESC
        LIMIT ? OFFSET ?
    """

    params.extend([limit, offset])

    with db.get_cursor() as cursor:
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
