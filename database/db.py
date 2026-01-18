"""Database connection and configuration module."""

import os
from contextlib import contextmanager
from typing import Generator

import psycopg
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


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
    except Exception:
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
            return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False
