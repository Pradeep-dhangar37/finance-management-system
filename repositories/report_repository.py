"""Report repository for financial reports and opening/closing records."""
from typing import List, Dict, Any, Optional
from db import Database

class ReportRepository:
    @staticmethod
    def get_first_loan_date(test: bool = False) -> Optional[Dict[str, Any]]:
        sql = "SELECT loan_application_date FROM loan_tbl ORDER BY loan_id ASC LIMIT 1"
        return Database.query_one(sql, test=test)

    @staticmethod
    def get_outstanding_by_date(from_date: Optional[str] = None, to_date: Optional[str] = None, test: bool = False) -> List[Dict[str, Any]]:
        sql = "SELECT * FROM loan_tbl WHERE 1=1"
        params = []
        if from_date and to_date:
            sql += " AND loan_application_date BETWEEN %s AND %s"
            params.extend([from_date, to_date])
        elif to_date:
            sql += " AND loan_application_date <= %s"
            params.append(to_date)
        sql += " ORDER BY loan_id ASC"
        return Database.query_all(sql, tuple(params) if params else None, test=test)

    @staticmethod
    def get_client_collections(loan_id: int, from_date: Optional[str] = None, to_date: Optional[str] = None, test: bool = False) -> List[Dict[str, Any]]:
        sql = "SELECT instalment_amt FROM collection_tbl WHERE loan_id = %s"
        params = [loan_id]
        if from_date and to_date:
            sql += " AND collect_date BETWEEN %s AND %s"
            params.extend([from_date, to_date])
        elif to_date:
            sql += " AND collect_date <= %s"
            params.append(to_date)
        return Database.query_all(sql, tuple(params), test=test)

    # Report 2: Opening/Closing Balance
    @staticmethod
    def add_report_one(data: Dict[str, Any], test: bool = False) -> int:
        sql = """
            INSERT INTO opclosingbalrep_tbl (opening_bal, total_collection, closing_bal, rdpayment, total_bal, ad_date)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        params = (data['opening_bal'], data['total_collection'], data['closing_bal'], data['rdpayment'], data['total_bal'], data['ad_date'])
        rid, _ = Database.execute(sql, params, test=test)
        return rid

    @staticmethod
    def get_report_one_all(test: bool = False) -> List[Dict[str, Any]]:
        sql = "SELECT * FROM opclosingbalrep_tbl ORDER BY id DESC"
        return Database.query_all(sql, test=test)

    @staticmethod
    def delete_report_one(record_id: int, test: bool = False) -> int:
        sql = "DELETE FROM opclosingbalrep_tbl WHERE id = %s"
        _, affected = Database.execute(sql, (record_id,), test=test)
        return affected

    @staticmethod
    def exists_report_one_date(ad_date: str, test: bool = False) -> bool:
        sql = "SELECT id FROM opclosingbalrep_tbl WHERE ad_date = %s LIMIT 1"
        return bool(Database.query_one(sql, (ad_date,), test=test))

    # Report 3: Total Balance & Disbursement
    @staticmethod
    def add_report_two(data: Dict[str, Any], test: bool = False) -> int:
        sql = """
            INSERT INTO reportstotal_tbl (total_disabesment, current_outstanding, difference_outstanding, client_disabsment, interest_amount, ad_date)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        params = (data['total_disabesment'], data['current_outstanding'], data['difference_outstanding'], data['client_disabsment'], data['interest_amount'], data['ad_date'])
        rid, _ = Database.execute(sql, params, test=test)
        return rid

    @staticmethod
    def get_report_two_all(test: bool = False) -> List[Dict[str, Any]]:
        sql = "SELECT * FROM reportstotal_tbl ORDER BY rid DESC"
        return Database.query_all(sql, test=test)

    @staticmethod
    def delete_report_two(record_id: int, test: bool = False) -> int:
        sql = "DELETE FROM reportstotal_tbl WHERE rid = %s"
        _, affected = Database.execute(sql, (record_id,), test=test)
        return affected

    @staticmethod
    def exists_report_two_date(ad_date: str, test: bool = False) -> bool:
        sql = "SELECT rid FROM reportstotal_tbl WHERE ad_date = %s LIMIT 1"
        return bool(Database.query_one(sql, (ad_date,), test=test))
