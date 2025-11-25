"""
Database connection module for Fluxion00API.

This module provides a simple interface to connect to the SQLite database
using raw SQL queries via the sqlite3 library.
"""

import sqlite3
import os
from pathlib import Path
from typing import Optional
from contextlib import contextmanager


class DatabaseConnection:
    """Manages SQLite database connections."""

    def __init__(self, db_path: Optional[str] = None, db_name: Optional[str] = None):
        """
        Initialize database connection parameters.

        Args:
            db_path: Path to database directory. If None, reads from PATH_TO_DATABASE env var.
            db_name: Database filename. If None, reads from NAME_DB env var.
        """
        self.db_path = db_path or os.getenv('PATH_TO_DATABASE')
        self.db_name = db_name or os.getenv('NAME_DB')

        if not self.db_path or not self.db_name:
            raise ValueError(
                "Database path and name must be provided either as arguments "
                "or through PATH_TO_DATABASE and NAME_DB environment variables"
            )

        self.full_path = Path(self.db_path) / self.db_name

    def get_connection(self) -> sqlite3.Connection:
        """
        Create and return a new database connection.

        Returns:
            sqlite3.Connection: Database connection object

        Raises:
            FileNotFoundError: If database file doesn't exist
            sqlite3.Error: If connection fails
        """
        if not self.full_path.exists():
            raise FileNotFoundError(f"Database file not found: {self.full_path}")

        # Enable row factory for dict-like access
        conn = sqlite3.connect(str(self.full_path))
        conn.row_factory = sqlite3.Row
        return conn

    @contextmanager
    def get_cursor(self):
        """
        Context manager for database operations.

        Yields:
            sqlite3.Cursor: Database cursor object

        Example:
            with db.get_cursor() as cursor:
                cursor.execute("SELECT * FROM table")
                results = cursor.fetchall()
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()


# Global database connection instance
db_connection = DatabaseConnection()


def get_db() -> DatabaseConnection:
    """
    Get the global database connection instance.

    Returns:
        DatabaseConnection: The global database connection instance
    """
    return db_connection
