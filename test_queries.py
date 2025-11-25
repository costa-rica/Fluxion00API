"""
Test script for database connection and query functions.

This script tests all the query functions for the ArticleApproveds table.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables (override=True to always use latest .env values)
load_dotenv(override=True)

# Import query functions
from src.queries.queries_approved_articles import (
    get_approved_articles_count,
    search_approved_articles_by_text,
    get_approved_articles_by_user,
    get_approved_articles_by_date_range,
    get_approved_article_by_id,
    get_all_approved_articles
)


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"{title}")
    print('='*60)


def test_database_connection():
    """Test database connection."""
    print_section("Testing Database Connection")

    try:
        from src.database.connection import get_db
        db = get_db()
        print(f"✓ Database path: {db.full_path}")
        print(f"✓ Database exists: {db.full_path.exists()}")

        if not db.full_path.exists():
            print("✗ ERROR: Database file not found!")
            return False

        # Test connection
        with db.get_cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"✓ Connection successful! Found {len(tables)} tables")
            print(f"  Tables: {[t['name'] for t in tables][:5]}...")  # Show first 5 tables

        return True
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False


def test_count_approved_articles():
    """Test counting approved articles."""
    print_section("Testing: Count Approved Articles")

    try:
        approved_count = get_approved_articles_count(is_approved=True)
        not_approved_count = get_approved_articles_count(is_approved=False)

        print(f"✓ Approved articles: {approved_count}")
        print(f"✓ Not approved articles: {not_approved_count}")
        print(f"✓ Total: {approved_count + not_approved_count}")
        return True
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False


def test_get_all_articles():
    """Test getting all articles."""
    print_section("Testing: Get All Approved Articles (Limited)")

    try:
        articles = get_all_approved_articles(is_approved=True, limit=5)
        print(f"✓ Retrieved {len(articles)} articles")

        if articles:
            print("\nFirst article:")
            for key, value in articles[0].items():
                if value and len(str(value)) > 100:
                    print(f"  {key}: {str(value)[:100]}...")
                else:
                    print(f"  {key}: {value}")
        else:
            print("  No articles found")

        return True
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False


def test_search_by_text():
    """Test text search functionality."""
    print_section("Testing: Search by Text")

    try:
        # Search for a common word (you may need to adjust this based on your data)
        search_terms = ["safety", "recall", "injury", "product"]

        for term in search_terms:
            results = search_approved_articles_by_text(
                search_text=term,
                is_approved=True,
                limit=3
            )
            print(f"✓ Search for '{term}': {len(results)} results")

            if results:
                print(f"  First result headline: {results[0].get('headlineForPdfReport', 'N/A')[:80]}...")
                break  # Stop after first successful search

        if not any(search_approved_articles_by_text(term, limit=1) for term in search_terms):
            print("  Note: No results found for common search terms")

        return True
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False


def test_get_by_user():
    """Test getting articles by user."""
    print_section("Testing: Get Articles by User")

    try:
        # First, get a valid user ID from an existing article
        articles = get_all_approved_articles(limit=1)

        if articles and articles[0]['userId']:
            user_id = articles[0]['userId']
            user_articles = get_approved_articles_by_user(
                user_id=user_id,
                is_approved=True,
                limit=5
            )
            print(f"✓ User ID {user_id} has {len(user_articles)} approved articles")
        else:
            print("  No articles with user IDs found to test")

        return True
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False


def test_get_by_date_range():
    """Test getting articles by date range."""
    print_section("Testing: Get Articles by Date Range")

    try:
        # Test with a wide date range
        articles = get_approved_articles_by_date_range(
            start_date='2020-01-01',
            end_date='2025-12-31',
            is_approved=True,
            limit=5
        )
        print(f"✓ Found {len(articles)} articles in date range 2020-2025")

        if articles:
            print(f"  First article created: {articles[0]['createdAt']}")

        return True
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False


def test_get_by_id():
    """Test getting a single article by ID."""
    print_section("Testing: Get Article by ID")

    try:
        # Get first article's ID
        articles = get_all_approved_articles(limit=1)

        if articles:
            article_id = articles[0]['id']
            article = get_approved_article_by_id(article_id)

            if article:
                print(f"✓ Successfully retrieved article ID {article_id}")
                print(f"  Headline: {article.get('headlineForPdfReport', 'N/A')[:80]}...")
            else:
                print(f"✗ Article ID {article_id} not found")
        else:
            print("  No articles available to test")

        return True
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("FLUXION00API - DATABASE QUERY TESTS")
    print("="*60)

    # Check if .env is loaded
    print(f"\nEnvironment variables loaded:")
    print(f"  PATH_TO_DATABASE: {os.getenv('PATH_TO_DATABASE')}")
    print(f"  NAME_DB: {os.getenv('NAME_DB')}")

    tests = [
        ("Database Connection", test_database_connection),
        ("Count Approved Articles", test_count_approved_articles),
        ("Get All Articles", test_get_all_articles),
        ("Search by Text", test_search_by_text),
        ("Get by User", test_get_by_user),
        ("Get by Date Range", test_get_by_date_range),
        ("Get by ID", test_get_by_id),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ FATAL ERROR in {test_name}: {e}")
            results.append((test_name, False))

    # Summary
    print_section("TEST SUMMARY")
    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")


if __name__ == "__main__":
    main()
