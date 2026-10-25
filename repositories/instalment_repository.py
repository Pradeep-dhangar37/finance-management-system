"""Instalment repository for scheduled payments and status."""
from typing import List, Dict, Any, Optional
from db import Database

class InstalmentRepository:
    @staticmethod
    def create_many(instalments: List[tuple], test: bool = False) -> int:
        sql = """
            INSERT INTO instalment_tbl (loan_id, instalment_amt, instalment_no, due_date, status)
            VALUES (%s, %s, %s, %s, 'unpaid')
        """
        return Database.execute_many(sql, instalments, test=test)

    @staticmethod
    def get_by_loan_id(loan_id: int, test: bool = False) -> List[Dict[str, Any]]:
        sql = "SELECT * FROM instalment_tbl WHERE loan_id = %s ORDER BY instalment_no ASC"
        return Database.query_all(sql, (loan_id,), test=test)

    @staticmethod
    def get_by_loan_and_no(loan_id: int, instalment_no: int, test: bool = False) -> Optional[Dict[str, Any]]:
        sql = "SELECT * FROM instalment_tbl WHERE loan_id = %s AND instalment_no = %s LIMIT 1"
        return Database.query_one(sql, (loan_id, instalment_no), test=test)

    @staticmethod
    def delete_by_loan_id(loan_id: int, test: bool = False) -> int:
        sql = "DELETE FROM instalment_tbl WHERE loan_id = %s"
        _, affected = Database.execute(sql, (loan_id,), test=test)
        return affected

    @staticmethod
    def mark_paid(loan_id: int, instalment_no: int, collect_date: str, test: bool = False) -> int:
        sql = """
            UPDATE instalment_tbl 
            SET status = 'paid', collect_date = %s 
            WHERE loan_id = %s AND instalment_no = %s
        """
        _, affected = Database.execute(sql, (collect_date, loan_id, instalment_no), test=test)
        return affected

    @staticmethod
    def revert_unpaid(loan_id: int, instalment_no: int, test: bool = False) -> int:
        sql = """
            UPDATE instalment_tbl 
            SET status = 'unpaid', collect_date = NULL 
            WHERE loan_id = %s AND instalment_no = %s
        """
        _, affected = Database.execute(sql, (loan_id, instalment_no), test=test)
        return affected

    @staticmethod
    def get_latest_paid(loan_id: int, test: bool = False) -> Optional[Dict[str, Any]]:
        sql = """
            SELECT * FROM instalment_tbl 
            WHERE loan_id = %s AND status = 'paid' 
            ORDER BY ins_id DESC LIMIT 1
        """
        return Database.query_one(sql, (loan_id,), test=test)

    @staticmethod
    def get_pending_by_date(date_str: str, test: bool = False) -> List[Dict[str, Any]]:
        sql = """
            SELECT i.*, l.client_name, l.loan_application_no, l.mobile
            FROM instalment_tbl i
            INNER JOIN loan_tbl l ON i.loan_id = l.loan_id
            WHERE i.due_date = %s AND i.status = 'unpaid' AND l.for_close != 'yes'
            ORDER BY i.ins_id ASC
        """
        return Database.query_all(sql, (date_str,), test=test)

    @staticmethod
    def get_pending_amount_by_date(date_str: str, test: bool = False) -> List[Dict[str, Any]]:
        sql = """
            SELECT i.instalment_amt, l.for_close
            FROM instalment_tbl i
            INNER JOIN loan_tbl l ON i.loan_id = l.loan_id
            WHERE i.due_date = %s AND i.status = 'unpaid' AND l.for_close != 'yes'
        """
        return Database.query_all(sql, (date_str,), test=test)
