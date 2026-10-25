"""User repository for authentication and profile management."""
from typing import Optional, Dict, Any
from db import Database

class UserRepository:
    @staticmethod
    def get_by_email(email: str, test: bool = False) -> Optional[Dict[str, Any]]:
        sql = "SELECT * FROM users_tbl WHERE email = %s LIMIT 1"
        return Database.query_one(sql, (email,), test=test)

    @staticmethod
    def get_by_id(user_id: int, test: bool = False) -> Optional[Dict[str, Any]]:
        sql = "SELECT * FROM users_tbl WHERE user_id = %s LIMIT 1"
        return Database.query_one(sql, (user_id,), test=test)

    @staticmethod
    def update_password(user_id: int, hashed_password: str, test: bool = False) -> int:
        sql = "UPDATE users_tbl SET password = %s WHERE user_id = %s"
        _, affected = Database.execute(sql, (hashed_password, user_id), test=test)
        return affected

    @staticmethod
    def create_user(username: str, email: str, hashed_password: str, test: bool = False) -> int:
        sql = "INSERT INTO users_tbl (username, email, password) VALUES (%s, %s, %s)"
        user_id, _ = Database.execute(sql, (username, email, hashed_password), test=test)
        return user_id
