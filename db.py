"""
Database connection and query execution module for Finance Management System.
Uses mysql.connector with explicit SQL queries and parameterized placeholders (%s).
"""
import logging
from contextlib import contextmanager
from typing import List, Dict, Any, Optional, Tuple
import mysql.connector
from mysql.connector import Error, pooling
from config import Config

logger = logging.getLogger('financemanagement.db')

class Database:
    _pool: Optional[pooling.MySQLConnectionPool] = None

    @classmethod
    def get_connection(cls, test: bool = False):
        """Obtain a MySQL connection using parameters from Config."""
        db_name = Config.TEST_DB_NAME if test else Config.DB_NAME
        user = Config.TEST_DB_USER if test else Config.DB_USER
        password = Config.TEST_DB_PASSWORD if test else Config.DB_PASSWORD
        
        return mysql.connector.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            database=db_name,
            user=user,
            password=password,
            autocommit=False,
            charset='utf8mb4'
        )

    @classmethod
    @contextmanager
    def transaction(cls, test: bool = False):
        """Context manager for database transactions with automatic commit/rollback."""
        conn = cls.get_connection(test=test)
        cursor = conn.cursor(dictionary=True)
        try:
            yield cursor, conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error("Transaction rolled back due to error: %s", e)
            raise e
        finally:
            cursor.close()
            conn.close()

    @classmethod
    def query_all(cls, sql: str, params: Optional[Tuple] = None, test: bool = False) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return all rows as list of dicts."""
        conn = cls.get_connection(test=test)
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(sql, params or ())
            rows = cursor.fetchall()
            return rows or []
        finally:
            cursor.close()
            conn.close()

    @classmethod
    def query_one(cls, sql: str, params: Optional[Tuple] = None, test: bool = False) -> Optional[Dict[str, Any]]:
        """Execute a SELECT query and return one row as dict or None."""
        conn = cls.get_connection(test=test)
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(sql, params or ())
            row = cursor.fetchone()
            return row
        finally:
            cursor.close()
            conn.close()

    @classmethod
    def execute(cls, sql: str, params: Optional[Tuple] = None, test: bool = False) -> Tuple[int, int]:
        """
        Execute an INSERT/UPDATE/DELETE query within an auto-committed transaction.
        Returns (lastrowid, rowcount).
        """
        with cls.transaction(test=test) as (cursor, conn):
            cursor.execute(sql, params or ())
            last_id = cursor.lastrowid
            affected = cursor.rowcount
            return last_id, affected

    @classmethod
    def execute_many(cls, sql: str, seq_params: List[Tuple], test: bool = False) -> int:
        """Execute multiple parameter sets in one transaction."""
        with cls.transaction(test=test) as (cursor, conn):
            cursor.executemany(sql, seq_params)
            return cursor.rowcount

    @classmethod
    def ping(cls, test: bool = False) -> bool:
        """Check if MySQL connection is healthy."""
        try:
            conn = cls.get_connection(test=test)
            conn.ping(reconnect=True, attempts=1, delay=0)
            conn.close()
            return True
        except Exception as e:
            logger.warning("Database ping failed: %s", e)
            return False
