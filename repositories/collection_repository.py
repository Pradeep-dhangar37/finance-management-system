"""Collection repository for collection transactions and receipts."""
from typing import List, Dict, Any, Optional
from db import Database

class CollectionRepository:
    @staticmethod
    def create(data: Dict[str, Any], test: bool = False) -> int:
        sql = """
            INSERT INTO collection_tbl (
                loan_id, instalment_amt, payment_date, remark, collect_date, instal_no, created
            ) VALUES (%s, %s, %s, %s, %s, %s, NOW())
        """
        params = (
            data['loan_id'], data['instalment_amt'], data['payment_date'],
            data.get('remark', ''), data['collect_date'], data.get('instal_no', 0)
        )
        coll_id, _ = Database.execute(sql, params, test=test)
        return coll_id

    @staticmethod
    def get_all(test: bool = False) -> List[Dict[str, Any]]:
        sql = """
            SELECT c.*, l.client_name, l.loan_application_no
            FROM collection_tbl c
            INNER JOIN loan_tbl l ON c.loan_id = l.loan_id
            ORDER BY c.collection_id DESC
        """
        return Database.query_all(sql, test=test)

    @staticmethod
    def get_by_date(date_str: str, test: bool = False) -> List[Dict[str, Any]]:
        sql = """
            SELECT c.*, l.client_name, l.loan_application_no
            FROM collection_tbl c
            INNER JOIN loan_tbl l ON c.loan_id = l.loan_id
            WHERE c.collect_date = %s
            ORDER BY c.collection_id DESC
        """
        return Database.query_all(sql, (date_str,), test=test)

    @staticmethod
    def get_today_amount(date_str: str, test: bool = False) -> List[Dict[str, Any]]:
        sql = """
            SELECT c.instalment_amt, l.for_close
            FROM collection_tbl c
            INNER JOIN loan_tbl l ON c.loan_id = l.loan_id
            WHERE c.collect_date = %s
        """
        return Database.query_all(sql, (date_str,), test=test)

    @staticmethod
    def get_today_distinct_loan_count(date_str: str, test: bool = False) -> List[Dict[str, Any]]:
        sql = "SELECT DISTINCT loan_id FROM collection_tbl WHERE collect_date = %s"
        return Database.query_all(sql, (date_str,), test=test)

    @staticmethod
    def get_receipt_details(collection_id: int, test: bool = False) -> Optional[Dict[str, Any]]:
        sql = """
            SELECT c.*, l.client_name, l.father_name, l.city_village, l.district,
                   l.mobile, l.aadhar_no, l.loan_application_no, l.loan_amount,
                   l.loan_intrest_amount, l.paid_amount, l.due_amount,
                   b.branch_name
            FROM collection_tbl c
            INNER JOIN loan_tbl l ON c.loan_id = l.loan_id
            LEFT JOIN branch_tbl b ON l.branch_id = b.branch_id
            WHERE c.collection_id = %s LIMIT 1
        """
        return Database.query_one(sql, (collection_id,), test=test)

    @staticmethod
    def get_by_loan_id(loan_id: int, test: bool = False) -> List[Dict[str, Any]]:
        sql = "SELECT * FROM collection_tbl WHERE loan_id = %s ORDER BY collection_id ASC"
        return Database.query_all(sql, (loan_id,), test=test)

    @staticmethod
    def count_by_loan_id(loan_id: int, test: bool = False) -> int:
        sql = "SELECT COUNT(*) AS total FROM collection_tbl WHERE loan_id = %s"
        row = Database.query_one(sql, (loan_id,), test=test)
        return row['total'] if row else 0

    @staticmethod
    def delete_by_loan_and_instal(loan_id: int, instal_no: int, test: bool = False) -> int:
        sql = "DELETE FROM collection_tbl WHERE loan_id = %s AND instal_no = %s"
        _, affected = Database.execute(sql, (loan_id, instal_no), test=test)
        return affected

    @staticmethod
    def get_for_ledger(loan_id: int, from_date: Optional[str] = None, to_date: Optional[str] = None, test: bool = False) -> List[Dict[str, Any]]:
        sql = "SELECT * FROM collection_tbl WHERE loan_id = %s"
        params = [loan_id]
        if from_date and to_date:
            sql += " AND collect_date BETWEEN %s AND %s"
            params.extend([from_date, to_date])
        sql += " ORDER BY collection_id ASC"
        return Database.query_all(sql, tuple(params), test=test)
