import unittest
from db import Database
from config import Config

class TestDatabaseConnectivity(unittest.TestCase):
    """Database connectivity and query execution tests."""

    def test_database_ping(self):
        """Test database connection health if MySQL is available."""
        is_connected = Database.ping()
        if not is_connected:
            self.skipTest(f"MySQL database '{Config.DB_NAME}' not reachable on {Config.DB_HOST}:{Config.DB_PORT}. "
                          "Please create database and configure .env as described in README.")
        
        # If connected, test basic query
        res = Database.query_one("SELECT 1 AS alive")
        self.assertIsNotNone(res)
        self.assertEqual(res['alive'], 1)

    def test_users_table_exists(self):
        """Verify users table structure if database is connected."""
        if not Database.ping():
            self.skipTest("Database not connected.")
        
        user = Database.query_one("SELECT email FROM users_tbl LIMIT 1")
        # May be None if empty, but query must not throw syntax or table missing error
        self.assertTrue(user is None or 'email' in user)

if __name__ == '__main__':
    unittest.main()
