"""Branch repository for branch master management."""
from typing import List, Dict, Any, Optional
from db import Database

class BranchRepository:
    @staticmethod
    def get_all(test: bool = False) -> List[Dict[str, Any]]:
        sql = "SELECT * FROM branch_tbl ORDER BY branch_id DESC"
        return Database.query_all(sql, test=test)

    @staticmethod
    def get_by_id(branch_id: int, test: bool = False) -> Optional[Dict[str, Any]]:
        sql = "SELECT * FROM branch_tbl WHERE branch_id = %s LIMIT 1"
        return Database.query_one(sql, (branch_id,), test=test)

    @staticmethod
    def get_by_name(branch_name: str, test: bool = False) -> Optional[Dict[str, Any]]:
        sql = "SELECT * FROM branch_tbl WHERE branch_name = %s LIMIT 1"
        return Database.query_one(sql, (branch_name,), test=test)

    @staticmethod
    def create(branch_name: str, ad_date: str, test: bool = False) -> int:
        sql = "INSERT INTO branch_tbl (branch_name, ad_date, created_at) VALUES (%s, %s, NOW())"
        branch_id, _ = Database.execute(sql, (branch_name, ad_date), test=test)
        return branch_id

    @staticmethod
    def update(branch_id: int, branch_name: str, test: bool = False) -> int:
        sql = "UPDATE branch_tbl SET branch_name = %s WHERE branch_id = %s"
        _, affected = Database.execute(sql, (branch_name, branch_id), test=test)
        return affected

    @staticmethod
    def count(test: bool = False) -> int:
        sql = "SELECT COUNT(*) AS total FROM branch_tbl"
        row = Database.query_one(sql, test=test)
        return row['total'] if row else 0
