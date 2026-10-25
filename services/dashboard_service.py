"""Dashboard metrics and chart aggregation service."""
from datetime import date
from decimal import Decimal
from typing import Dict, Any
from repositories.branch_repository import BranchRepository
from repositories.loan_repository import LoanRepository
from repositories.collection_repository import CollectionRepository
from repositories.instalment_repository import InstalmentRepository

class DashboardService:
    @staticmethod
    def get_metrics(test: bool = False) -> Dict[str, Any]:
        today_str = date.today().strftime('%Y-%m-%d')
        total_branch = BranchRepository.count(test=test)
        total_loan = LoanRepository.count(test=test)

        # Collections made today
        today_collections = CollectionRepository.get_today_amount(today_str, test=test)
        today_collect_amt = sum(Decimal(str(r['instalment_amt'])) for r in today_collections) if today_collections else Decimal('0.00')
        today_collect_count_list = CollectionRepository.get_today_distinct_loan_count(today_str, test=test)
        today_collect_count = len(today_collect_count_list) if today_collect_count_list else 0

        # Pending collections due today
        today_pending = InstalmentRepository.get_pending_amount_by_date(today_str, test=test)
        today_pending_amt = sum(Decimal(str(r['instalment_amt'])) for r in today_pending) if today_pending else Decimal('0.00')
        today_pending_count = len(today_pending) if today_pending else 0

        return {
            'totalBranch': total_branch,
            'totalLoan': total_loan,
            'todayCollectAmount': float(today_collect_amt),
            'todayPendingAmount': float(today_pending_amt),
            'todayCollect': today_collect_count,
            'todayPendingCollect': today_pending_count,
        }
