"""Business logic for collections, installments payment, and receipt generation."""
from datetime import date
from decimal import Decimal
from typing import Dict, Any, Tuple
from repositories.loan_repository import LoanRepository
from repositories.instalment_repository import InstalmentRepository
from repositories.collection_repository import CollectionRepository
from services.loan_service import parse_date_str

class CollectionService:
    @staticmethod
    def add_collection(loan_id: int, instalment_amt: Decimal, payment_date: str, remark: str, test: bool = False) -> Tuple[bool, str, int]:
        loan = LoanRepository.get_by_id(loan_id, test=test)
        if not loan:
            return False, "Loan record not found.", 0
        if int(loan.get('status', 1)) != 1:
            return False, "Unapprove Loan.", 0

        current_due = Decimal(str(loan['due_amount']))
        if current_due < instalment_amt or current_due <= 0:
            return False, "Loan Amount Already Paid.", 0

        today_str = date.today().strftime('%Y-%m-%d')
        pay_date_str = parse_date_str(payment_date)

        paid_amount = Decimal(str(loan['paid_amount'])) + instalment_amt
        new_due = current_due - instalment_amt
        paid_instalment = int(loan['paid_instalment']) + 1
        due_instalment = max(0, int(loan['due_instalment']) - 1)

        loan_update = {
            'paid_amount': float(paid_amount),
            'due_amount': float(new_due),
            'paid_instalment': paid_instalment,
            'due_instalment': due_instalment,
            'coll_date': today_str
        }
        LoanRepository.update(loan_id, loan_update, test=test)

        # Update instalment in instalment_tbl
        InstalmentRepository.mark_paid(loan_id, paid_instalment, today_str, test=test)

        # Record in collection_tbl
        coll_id = CollectionRepository.create({
            'loan_id': loan_id,
            'instalment_amt': float(instalment_amt),
            'payment_date': pay_date_str,
            'remark': remark,
            'collect_date': today_str,
            'instal_no': paid_instalment
        }, test=test)

        return True, "Collection Added Successfully.", coll_id

    @staticmethod
    def delete_instalment(loan_id: int, instal_no: int, test: bool = False) -> Tuple[bool, str]:
        inst = InstalmentRepository.get_by_loan_and_no(loan_id, instal_no, test=test)
        if not inst or inst.get('status') != 'paid':
            return False, "Instalment Already Delete."

        # Verify it's the latest paid installment to maintain sequential integrity
        latest_paid = InstalmentRepository.get_latest_paid(loan_id, test=test)
        if latest_paid and latest_paid['instalment_no'] != instal_no:
            return False, "Can only delete the most recent paid installment."

        loan = LoanRepository.get_by_id(loan_id, test=test)
        instalment_amount = Decimal(str(inst['instalment_amt']))
        paid_amount = Decimal(str(loan['paid_amount'])) - instalment_amount
        due_amount = Decimal(str(loan['due_amount'])) + instalment_amount
        paid_instalment = int(loan['paid_instalment']) - 1
        due_instalment = int(loan['due_instalment']) + 1

        CollectionRepository.delete_by_loan_and_instal(loan_id, instal_no, test=test)
        InstalmentRepository.revert_unpaid(loan_id, instal_no, test=test)
        LoanRepository.update(loan_id, {
            'paid_amount': float(paid_amount),
            'due_amount': float(due_amount),
            'paid_instalment': paid_instalment,
            'due_instalment': due_instalment
        }, test=test)

        return True, "Instalment Delete Successfully."

    @staticmethod
    def get_receipt(collection_id: int, test: bool = False) -> Dict[str, Any]:
        receipt = CollectionRepository.get_receipt_details(collection_id, test=test)
        if receipt:
            inst_amt = Decimal(str(receipt['instalment_amt']))
            due_amt = Decimal(str(receipt['due_amount']))
            receipt['prev_bal'] = float(inst_amt + due_amt)
            receipt['curr_bal'] = float(due_amt)
        return receipt
