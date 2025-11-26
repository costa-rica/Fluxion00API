"""
Read-only database connection for LLM-generated SQL queries.

This module provides a secure, read-only database connection that prevents
any data modification operations from LLM-generated SQL queries.
"""

import sqlite3
from typing import Optional
from contextlib import contextmanager
from .connection import DatabaseConnection


class ReadOnlyDatabaseConnection(DatabaseConnection):
    """
    Read-only database connection for executing untrusted SQL queries.

    Extends DatabaseConnection with additional safety measures for
    LLM-generated queries.
    """

    def __init__(self, db_path: str, db_name: str):
        """
        Initialize read-only database connection.

        Args:
            db_path: Path to database directory
            db_name: Database filename
        """
        super().__init__(db_path, db_name)
        self._readonly_connection: Optional[sqlite3.Connection] = None

    def connect(self) -> sqlite3.Connection:
        """
        Create a read-only database connection.

        Returns:
            sqlite3.Connection: Read-only database connection
        """
        if self._readonly_connection is None:
            # Open connection in read-only mode
            db_uri = f"file:{self.full_path}?mode=ro"
            self._readonly_connection = sqlite3.connect(
                db_uri,
                uri=True,
                check_same_thread=False
            )

            # Enable query_only pragma for extra safety
            # This prevents write operations at SQLite engine level
            try:
                self._readonly_connection.execute("PRAGMA query_only = ON")
            except sqlite3.OperationalError:
                # Some SQLite versions don't support query_only pragma
                # The read-only file mode is still enforced
                pass

            # Return rows as dictionaries
            self._readonly_connection.row_factory = sqlite3.Row

        return self._readonly_connection

    @contextmanager
    def get_cursor(self):
        """
        Get a cursor from the read-only connection.

        Yields:
            sqlite3.Cursor: Database cursor for read-only operations
        """
        conn = self.connect()
        cursor = conn.cursor()
        try:
            yield cursor
        finally:
            cursor.close()

    def close(self):
        """Close the read-only database connection."""
        if self._readonly_connection:
            self._readonly_connection.close()
            self._readonly_connection = None


# Global read-only database instance
_readonly_db: Optional[ReadOnlyDatabaseConnection] = None


def get_readonly_db() -> ReadOnlyDatabaseConnection:
    """
    Get the global read-only database connection instance.

    Returns:
        ReadOnlyDatabaseConnection: Read-only database connection
    """
    global _readonly_db

    if _readonly_db is None:
        from .connection import get_db

        # Use same database path as the main connection
        main_db = get_db()
        _readonly_db = ReadOnlyDatabaseConnection(
            db_path=main_db.db_path,
            db_name=main_db.db_name
        )

    return _readonly_db
