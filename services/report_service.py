"""Financial reporting services matching Astha Finance reports 1, 2, and 3."""
from datetime import date
from decimal import Decimal
from typing import Dict, Any, List, Optional
from repositories.report_repository import ReportRepository
from services.loan_service import parse_date_str

class ReportService:
    @staticmethod
    def get_outstanding_report(to_date_str: str, from_date_str: Optional[str] = '2022-04-01', test: bool = False) -> List[Dict[str, Any]]:
        t_date = parse_date_str(to_date_str)
        f_date = parse_date_str(from_date_str)
        loans = ReportRepository.get_outstanding_by_date(f_date, t_date, test=test)

        result = []
        for loan in loans:
            coll_entries = ReportRepository.get_client_collections(loan['loan_id'], f_date, t_date, test=test)
            receipt_total = sum(Decimal(str(c['instalment_amt'])) for c in coll_entries) if coll_entries else Decimal('0.00')
            loan_intrest = Decimal(str(loan['loan_intrest_amount']))
            balance = loan_intrest - receipt_total
            balance_amt = abs(balance)
            
            # Match original condition: display if balance != 0
            if balance_amt != Decimal('0.00'):
                loan_copy = dict(loan)
                loan_copy['receipt_total'] = float(receipt_total)
                loan_copy['balance_amount'] = float(balance_amt)
                loan_copy['dr_cr'] = 'Dr.' if Decimal(str(loan.get('due_amount', 0))) >= 0 else 'Cr.'
                result.append(loan_copy)

        return result
