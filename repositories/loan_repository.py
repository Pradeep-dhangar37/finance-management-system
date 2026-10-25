"""Loan repository for loan creation, updates, and tracking."""
from typing import List, Dict, Any, Optional
from db import Database

class LoanRepository:
    @staticmethod
    def create(data: Dict[str, Any], test: bool = False) -> int:
        sql = """
            INSERT INTO loan_tbl (
                branch_id, client_name, father_name, city_village, district,
                mobile, aadhar_no, loan_application_no, loan_application_date,
                loan_amount, loan_intrest_amount, instalment, instalment_amount,
                paid_amount, due_amount, paid_instalment, due_instalment,
                emi_start_date, status, for_close
            ) VALUES (
                %(branch_id)s, %(client_name)s, %(father_name)s, %(city_village)s, %(district)s,
                %(mobile)s, %(aadhar_no)s, %(loan_application_no)s, %(loan_application_date)s,
                %(loan_amount)s, %(loan_intrest_amount)s, %(instalment)s, %(instalment_amount)s,
                %(paid_amount)s, %(due_amount)s, %(paid_instalment)s, %(due_instalment)s,
                %(emi_start_date)s, %(status)s, %(for_close)s
            )
        """
        # Convert dict to tuple in exact placeholder order
        params = (
            data['branch_id'], data['client_name'], data['father_name'], data['city_village'], data['district'],
            data['mobile'], data['aadhar_no'], data['loan_application_no'], data['loan_application_date'],
            data['loan_amount'], data['loan_intrest_amount'], data['instalment'], data['instalment_amount'],
            data.get('paid_amount', 0.0), data.get('due_amount', data['loan_intrest_amount']),
            data.get('paid_instalment', 0), data.get('due_instalment', data['instalment']),
            data['emi_start_date'], data.get('status', 1), data.get('for_close', 'no')
        )
        insert_sql = """
            INSERT INTO loan_tbl (
                branch_id, client_name, father_name, city_village, district,
                mobile, aadhar_no, loan_application_no, loan_application_date,
                loan_amount, loan_intrest_amount, instalment, instalment_amount,
                paid_amount, due_amount, paid_instalment, due_instalment,
                emi_start_date, status, for_close
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        loan_id, _ = Database.execute(insert_sql, params, test=test)
        return loan_id

    @staticmethod
    def get_by_id(loan_id: int, test: bool = False) -> Optional[Dict[str, Any]]:
        sql = """
            SELECT l.*, b.branch_name 
            FROM loan_tbl l
            LEFT JOIN branch_tbl b ON l.branch_id = b.branch_id
            WHERE l.loan_id = %s LIMIT 1
        """
        return Database.query_one(sql, (loan_id,), test=test)

    @staticmethod
    def get_all(test: bool = False) -> List[Dict[str, Any]]:
        sql = """
            SELECT l.*, b.branch_name
            FROM loan_tbl l
            LEFT JOIN branch_tbl b ON l.branch_id = b.branch_id
            ORDER BY l.loan_id DESC
        """
        return Database.query_all(sql, test=test)

    @staticmethod
    def get_dropdown_list(test: bool = False) -> List[Dict[str, Any]]:
        sql = "SELECT loan_id, loan_application_no, client_name, for_close, status FROM loan_tbl ORDER BY loan_id DESC"
        return Database.query_all(sql, test=test)

    @staticmethod
    def get_latest_application_no(test: bool = False) -> Optional[str]:
        sql = "SELECT loan_application_no FROM loan_tbl ORDER BY loan_id DESC LIMIT 1"
        row = Database.query_one(sql, test=test)
        return row['loan_application_no'] if row else None

    @staticmethod
    def count(test: bool = False) -> int:
        sql = "SELECT COUNT(*) AS total FROM loan_tbl"
        row = Database.query_one(sql, test=test)
        return row['total'] if row else 0

    @staticmethod
    def get_due_loans(test: bool = False) -> List[Dict[str, Any]]:
        sql = """
            SELECT l.*, b.branch_name
            FROM loan_tbl l
            LEFT JOIN branch_tbl b ON l.branch_id = b.branch_id
            WHERE l.due_amount > 0
            ORDER BY l.loan_id DESC
        """
        return Database.query_all(sql, test=test)

    @staticmethod
    def update(loan_id: int, data: Dict[str, Any], test: bool = False) -> int:
        set_clauses = []
        values = []
        for k, v in data.items():
            set_clauses.append(f"`{k}` = %s")
            values.append(v)
        values.append(loan_id)
        sql = f"UPDATE loan_tbl SET {', '.join(set_clauses)} WHERE loan_id = %s"
        _, affected = Database.execute(sql, tuple(values), test=test)
        return affected

    @staticmethod
    def delete(loan_id: int, test: bool = False) -> int:
        sql = "DELETE FROM loan_tbl WHERE loan_id = %s"
        _, affected = Database.execute(sql, (loan_id,), test=test)
        return affected

    @staticmethod
    def set_status(loan_id: int, status: int, test: bool = False) -> int:
        sql = "UPDATE loan_tbl SET status = %s WHERE loan_id = %s"
        _, affected = Database.execute(sql, (status, loan_id), test=test)
        return affected
