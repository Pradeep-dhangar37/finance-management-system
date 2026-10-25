"""Ledger report service providing transaction histories and running balances."""
from typing import Dict, Any, List, Optional
from repositories.loan_repository import LoanRepository
from repositories.collection_repository import CollectionRepository
from services.loan_service import parse_date_str

class LedgerService:
    @staticmethod
    def get_ledger(loan_id: int, from_date: Optional[str] = None, to_date: Optional[str] = None, test: bool = False) -> Dict[str, Any]:
        loan = LoanRepository.get_by_id(loan_id, test=test)
        if not loan:
            return {'loan': None, 'collections': [], 'ledger_entries': []}

        f_date = parse_date_str(from_date) if from_date else None
        t_date = parse_date_str(to_date) if to_date else None

        collections = CollectionRepository.get_for_ledger(loan_id, f_date, t_date, test=test)
        return {
            'loan': loan,
            'collections': collections
        }
