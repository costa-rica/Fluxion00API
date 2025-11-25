"""
Article-related tools for the Fluxion00API agent.

This module provides tool wrappers around the ArticleApproveds query functions,
making them accessible to the agent for answering questions about articles.
"""

from typing import List, Dict, Any, Optional
from src.queries.queries_approved_articles import (
    get_approved_articles_count,
    search_approved_articles_by_text,
    get_approved_articles_by_user,
    get_approved_articles_by_date_range,
    get_approved_article_by_id,
    get_all_approved_articles
)
from .tools import ToolRegistry, ToolParameter


def register_article_tools(registry: ToolRegistry) -> None:
    """
    Register all article-related tools with the registry.

    Args:
        registry: Tool registry to register tools with
    """

    # Tool 1: Count approved articles
    registry.register_function(
        name="count_approved_articles",
        description=(
            "Get the count of approved or not-approved articles in the ArticleApproveds table. "
            "Use this when the user asks how many articles have been approved or rejected."
        ),
        function=get_approved_articles_count,
        parameters=[
            ToolParameter(
                name="is_approved",
                type="boolean",
                description="True to count approved articles, False to count rejected articles",
                required=False,
                default=True
            )
        ],
        category="articles"
    )

    # Tool 2: Search articles by text
    registry.register_function(
        name="search_approved_articles",
        description=(
            "Search for articles by text content across headlines, publication names, "
            "article text, and knowledge manager notes. Use this when the user wants to "
            "find articles about a specific topic or keyword."
        ),
        function=search_approved_articles_by_text,
        parameters=[
            ToolParameter(
                name="search_text",
                type="string",
                description="Text to search for in articles",
                required=True
            ),
            ToolParameter(
                name="is_approved",
                type="boolean",
                description="Filter by approval status (True=approved, False=rejected, None=all)",
                required=False,
                default=True
            ),
            ToolParameter(
                name="limit",
                type="integer",
                description="Maximum number of results to return",
                required=False,
                default=10
            )
        ],
        category="articles"
    )

    # Tool 3: Get articles by user
    registry.register_function(
        name="get_articles_by_user",
        description=(
            "Get articles approved or reviewed by a specific user. "
            "Use this when the user asks about articles associated with a particular user ID."
        ),
        function=get_approved_articles_by_user,
        parameters=[
            ToolParameter(
                name="user_id",
                type="integer",
                description="ID of the user who approved the articles",
                required=True
            ),
            ToolParameter(
                name="is_approved",
                type="boolean",
                description="Filter by approval status (True=approved, False=rejected, None=all)",
                required=False,
                default=True
            ),
            ToolParameter(
                name="limit",
                type="integer",
                description="Maximum number of results to return",
                required=False,
                default=10
            )
        ],
        category="articles"
    )

    # Tool 4: Get articles by date range
    registry.register_function(
        name="get_articles_by_date_range",
        description=(
            "Get articles within a specific date range. "
            "Use this when the user asks about articles from a particular time period."
        ),
        function=get_approved_articles_by_date_range,
        parameters=[
            ToolParameter(
                name="start_date",
                type="string",
                description="Start date in 'YYYY-MM-DD' format (e.g., '2024-01-01')",
                required=False,
                default=None
            ),
            ToolParameter(
                name="end_date",
                type="string",
                description="End date in 'YYYY-MM-DD' format (e.g., '2024-12-31')",
                required=False,
                default=None
            ),
            ToolParameter(
                name="is_approved",
                type="boolean",
                description="Filter by approval status (True=approved, False=rejected, None=all)",
                required=False,
                default=True
            ),
            ToolParameter(
                name="limit",
                type="integer",
                description="Maximum number of results to return",
                required=False,
                default=10
            )
        ],
        category="articles"
    )

    # Tool 5: Get article by ID
    registry.register_function(
        name="get_article_by_id",
        description=(
            "Get a specific article by its ArticleApproved ID. "
            "Use this when the user asks about a specific article by ID number."
        ),
        function=get_approved_article_by_id,
        parameters=[
            ToolParameter(
                name="article_approved_id",
                type="integer",
                description="ID of the ArticleApproved record",
                required=True
            )
        ],
        category="articles"
    )

    # Tool 6: Get all approved articles (paginated)
    registry.register_function(
        name="list_approved_articles",
        description=(
            "Get a list of approved articles with pagination. "
            "Use this when the user wants to see a list of articles or browse through them."
        ),
        function=get_all_approved_articles,
        parameters=[
            ToolParameter(
                name="is_approved",
                type="boolean",
                description="Filter by approval status (True=approved, False=rejected, None=all)",
                required=False,
                default=True
            ),
            ToolParameter(
                name="limit",
                type="integer",
                description="Maximum number of results to return",
                required=False,
                default=10
            ),
            ToolParameter(
                name="offset",
                type="integer",
                description="Number of records to skip for pagination",
                required=False,
                default=0
            )
        ],
        category="articles"
    )


def format_article_for_display(article: Dict[str, Any]) -> str:
    """
    Format an article dictionary for display to the user.

    Args:
        article: Article dictionary from query

    Returns:
        str: Formatted article string
    """
    headline = article.get('headlineForPdfReport', 'No headline')
    publication = article.get('publicationNameForPdfReport', 'Unknown')
    date = article.get('publicationDateForPdfReport', 'Unknown date')
    url = article.get('urlForPdfReport', 'No URL')

    # Truncate text if too long
    text = article.get('textForPdfReport', '')
    if text and len(text) > 200:
        text = text[:200] + "..."

    return f"""
**{headline}**
Publication: {publication}
Date: {date}
URL: {url}
{f"Text: {text}" if text else ""}
""".strip()


def format_articles_list(articles: List[Dict[str, Any]], max_display: int = 5) -> str:
    """
    Format a list of articles for display to the user.

    Args:
        articles: List of article dictionaries
        max_display: Maximum number of articles to display in full detail

    Returns:
        str: Formatted articles list
    """
    if not articles:
        return "No articles found."

    result = f"Found {len(articles)} article(s).\n\n"

    # Display detailed info for first few articles
    for i, article in enumerate(articles[:max_display]):
        result += f"--- Article {i + 1} ---\n"
        result += format_article_for_display(article)
        result += "\n\n"

    # If there are more articles, just mention them
    if len(articles) > max_display:
        remaining = len(articles) - max_display
        result += f"... and {remaining} more article(s)."

    return result.strip()
