"""Database connection and configuration module.

Function Lineage
----------------
The functions in this module have the following call hierarchy:

    test_connection()
        └── get_cursor()
            └── get_db_connection()
                └── get_connection()
                    └── get_database_url()

Function Dependencies:
- get_database_url() - Base function that retrieves database URL from environment
- get_connection() - Creates a connection using get_database_url()
- get_db_connection() - Context manager wrapping get_connection() with auto-cleanup
- get_cursor() - Higher-level context manager providing both connection and cursor
- test_connection() - Utility function using get_cursor() to verify connectivity

Recommended Usage:
- Use get_cursor() for most database operations (handles connection, cursor, and cleanup)
- Use get_db_connection() when you need direct connection access
- Use get_connection() only when manual connection management is required

Key Differences Between Connection Functions
---------------------------------------------

get_connection():
    - Returns: Raw psycopg.Connection object
    - Resource Management: MANUAL - You must close the connection yourself
    - Transaction Management: MANUAL - You must call commit() or rollback()
    - Error Handling: MANUAL - No automatic rollback on errors
    - Use When: You need fine-grained control over connection lifecycle, or when
      integrating with code that expects a connection object

get_db_connection():
    - Returns: psycopg.Connection via context manager
    - Resource Management: AUTOMATIC - Connection closed on context exit
    - Transaction Management: AUTOMATIC - Commits on success, rolls back on error
    - Error Handling: AUTOMATIC - Rolls back transaction if exception occurs
    - Use When: You need direct connection access (e.g., for multiple cursors,
      connection-level operations, or passing to other functions) but want
      automatic cleanup and transaction handling

get_cursor():
    - Returns: psycopg.Cursor via context manager
    - Resource Management: AUTOMATIC - Both cursor and connection cleaned up
    - Transaction Management: AUTOMATIC - Commits on success, rolls back on error
    - Error Handling: AUTOMATIC - Rolls back transaction if exception occurs
    - Use When: Standard database operations where you only need one cursor
      (this is the RECOMMENDED approach for most use cases)

Summary:
    get_cursor()        ← RECOMMENDED: Simplest, handles everything automatically
    get_db_connection() ← Use when you need the connection object directly
    get_connection()    ← Use only when you need manual control
"""

import os
from contextlib import contextmanager
from typing import Generator

import psycopg
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()
logger = logging.getLogger(__name__)

def get_database_url() -> str:
    """Get database URL from environment variables."""
    return os.getenv(
        "DATABASE_URL",
        "postgresql://mtguser:mtgpassword@localhost:5432/mtgcards_db"
    )


def get_connection() -> psycopg.Connection:
    """
    Create and return a new database connection.
    
    Returns:
        psycopg Connection object
        
    Example:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM sets")
                results = cur.fetchall()
        finally:
            conn.close()
    """
    return psycopg.connect(get_database_url())


@contextmanager
def get_db_connection() -> Generator[psycopg.Connection, None, None]:
    """
    Context manager for database connections.
    Automatically handles connection cleanup.
    
    Yields:
        psycopg Connection object
        
    Example:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM sets")
                results = cur.fetchall()
    """
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except psycopg.Error:
        conn.rollback()
        raise
    finally:
        conn.close()


@contextmanager
def get_cursor() -> Generator[psycopg.Cursor, None, None]:
    """
    Context manager that provides both connection and cursor.
    Automatically handles commit/rollback and cleanup.
    
    Yields:
        psycopg Cursor object
        
    Example:
        with get_cursor() as cur:
            cur.execute("SELECT * FROM sets")
            results = cur.fetchall()
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            yield cursor
        finally:
            cursor.close()


def test_connection() -> bool:
    """
    Test the database connection.
    
    Returns:
        True if connection successful, False otherwise
    """
    try:
        with get_cursor() as cur:
            cur.execute("SELECT 1")
            logger.info("Database connection successful.")
            return True
    except psycopg.Error as e:
        logger.info(f"Database connection failed: {e}")
        return False
