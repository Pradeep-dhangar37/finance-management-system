"""Business logic and calculations for Loans and Instalments."""
from datetime import datetime, date
from decimal import Decimal, ROUND_HALF_UP
import re
from typing import Dict, Any, List, Tuple
from repositories.loan_repository import LoanRepository
from repositories.instalment_repository import InstalmentRepository
from repositories.collection_repository import CollectionRepository
from repositories.branch_repository import BranchRepository

def add_months(orig_date: date, months: int) -> date:
    """Accurately add months to a date matching monthly installments."""
    year = orig_date.year + (orig_date.month + months - 1) // 12
    month = (orig_date.month + months - 1) % 12 + 1
    # Day handling
    import calendar
    max_day = calendar.monthrange(year, month)[1]
    day = min(orig_date.day, max_day)
    return date(year, month, day)

def parse_date_str(val: Any) -> str:
    """Parse date input in format dd-mm-yyyy or yyyy-mm-dd to yyyy-mm-dd."""
    if isinstance(val, (datetime, date)):
        return val.strftime('%Y-%m-%d')
    s = str(val).strip()
    for fmt in ('%d-%m-%Y', '%Y-%m-%d', '%d/%m/%Y', '%Y/%m/%d'):
        try:
            return datetime.strptime(s, fmt).strftime('%Y-%m-%d')
        except ValueError:
            pass
    return s

class LoanService:
    @staticmethod
    def calculate_installment_amount(loan_intrest_amount, instalments: int) -> Decimal:
        if instalments <= 0:
            return Decimal('0.00')
        return (Decimal(str(loan_intrest_amount)) / Decimal(instalments)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    @staticmethod
    def calculate_due_dates(emi_start_date_str: str, instalments: int) -> List[str]:
        parsed = parse_date_str(emi_start_date_str)
        emi_start = datetime.strptime(parsed, '%Y-%m-%d').date()
        due_dates = []
        for i in range(1, instalments + 1):
            due_dates.append(add_months(emi_start, i - 1).strftime('%Y-%m-%d'))
        return due_dates

    @staticmethod
    def validate_loan_data(data: Dict[str, Any], is_edit: bool = False, existing_loan: Dict[str, Any] = None) -> List[str]:
        errors = []
        if not data.get('branch_id') and not is_edit:
            errors.append("Branch Name is required.")
        if not data.get('client_name', '').strip():
            errors.append("Client Name is required.")
        if not data.get('father_name', '').strip():
            errors.append("Father's / Husband Name is required.")
        if not data.get('city_village', '').strip():
            errors.append("City/Village is required.")
        if not data.get('district', '').strip():
            errors.append("District is required.")
        
        mobile = str(data.get('mobile', '')).strip()
        if not mobile:
            errors.append("Mobile Number is required.")
        elif not re.match(r'^[6-9]\d{9}$', mobile):
            errors.append("Mobile Number must be 10 digits starting with 6-9.")
        
        aadhar = str(data.get('aadhar_no', '')).strip()
        if not aadhar:
            errors.append("Aadhar Number is required.")
        elif len(aadhar) != 12 or not aadhar.isdigit():
            errors.append("Aadhar Number must be exactly 12 digits.")

        if not is_edit:
            try:
                loan_amt = Decimal(str(data.get('loan_amount', '0')))
                interest_amt = Decimal(str(data.get('loan_intrest_amount', '0')))
                instalments = int(data.get('instalment', '0'))
                if loan_amt <= 0:
                    errors.append("Loan Amount must be greater than zero.")
                if interest_amt <= 0:
                    errors.append("Loan Interest Amount must be greater than zero.")
                if interest_amt < loan_amt:
                    errors.append("Loan interest amount is less than the loan amount.")
                if instalments <= 0:
                    errors.append("Number of instalments must be at least 1.")
            except Exception:
                errors.append("Invalid numerical values for loan amounts or instalments.")

            if not data.get('emi_start_date'):
                errors.append("EMI Start Date is required.")
            if not data.get('loan_application_date'):
                errors.append("Loan Application Date is required.")

        return errors

    @staticmethod
    def get_next_application_no(test: bool = False) -> str:
        latest = LoanRepository.get_latest_application_no(test=test)
        if latest and latest.isdigit():
            return str(int(latest) + 1)
        return "1001"

    @classmethod
    def create_loan(cls, data: Dict[str, Any], test: bool = False) -> Tuple[int, List[str]]:
        errors = cls.validate_loan_data(data, is_edit=False)
        if errors:
            return 0, errors

        loan_amount = Decimal(str(data['loan_amount']))
        loan_intrest_amount = Decimal(str(data['loan_intrest_amount']))
        instalments = int(data['instalment'])
        instalment_amount = (loan_intrest_amount / Decimal(instalments)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        app_no = data.get('loan_application_no') or cls.get_next_application_no(test=test)
        app_date = parse_date_str(data['loan_application_date'])
        emi_start_date_str = parse_date_str(data['emi_start_date'])
        emi_start = datetime.strptime(emi_start_date_str, '%Y-%m-%d').date()

        loan_record = {
            'branch_id': int(data['branch_id']),
            'client_name': data['client_name'].strip(),
            'father_name': data['father_name'].strip(),
            'city_village': data['city_village'].strip(),
            'district': data['district'].strip(),
            'mobile': data['mobile'].strip(),
            'aadhar_no': data['aadhar_no'].strip(),
            'loan_application_no': app_no,
            'loan_application_date': app_date,
            'loan_amount': float(loan_amount),
            'loan_intrest_amount': float(loan_intrest_amount),
            'instalment': instalments,
            'instalment_amount': float(instalment_amount),
            'paid_amount': 0.0,
            'due_amount': float(loan_intrest_amount),
            'paid_instalment': 0,
            'due_instalment': instalments,
            'emi_start_date': emi_start_date_str,
            'status': 1,
            'for_close': 'no'
        }

        loan_id = LoanRepository.create(loan_record, test=test)

        # Generate scheduled instalments matching original Astha Finance month-by-month calculation
        # i=1: due_date = emi_start; i=2: emi_start + 1 month, etc.
        instalments_to_insert = []
        for i in range(1, instalments + 1):
            due_date = add_months(emi_start, i - 1)
            instalments_to_insert.append((
                loan_id, float(instalment_amount), i, due_date.strftime('%Y-%m-%d')
            ))
        InstalmentRepository.create_many(instalments_to_insert, test=test)

        return loan_id, []

    @classmethod
    def edit_loan(cls, loan_id: int, data: Dict[str, Any], test: bool = False) -> Tuple[bool, List[str]]:
        existing = LoanRepository.get_by_id(loan_id, test=test)
        if not existing:
            return False, ["Loan record not found."]

        errors = cls.validate_loan_data(data, is_edit=True, existing_loan=existing)
        if errors:
            return False, errors

        update_dict = {
            'client_name': data['client_name'].strip(),
            'father_name': data['father_name'].strip(),
            'city_village': data['city_village'].strip(),
            'district': data['district'].strip(),
            'mobile': data['mobile'].strip(),
            'aadhar_no': data['aadhar_no'].strip(),
        }

        # If zero installments have been paid yet, financial recalculation is permitted
        if int(existing.get('paid_instalment', 0)) == 0 and 'loan_intrest_amount' in data and 'instalment' in data:
            loan_amount = Decimal(str(data.get('loan_amount', existing['loan_amount'])))
            loan_intrest_amount = Decimal(str(data['loan_intrest_amount']))
            instalments = int(data['instalment'])
            instalment_amount = (loan_intrest_amount / Decimal(instalments)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            emi_start_date_str = parse_date_str(data.get('emi_start_date', existing['emi_start_date']))
            emi_start = datetime.strptime(emi_start_date_str, '%Y-%m-%d').date()

            update_dict.update({
                'loan_amount': float(loan_amount),
                'loan_intrest_amount': float(loan_intrest_amount),
                'instalment': instalments,
                'instalment_amount': float(instalment_amount),
                'due_amount': float(loan_intrest_amount),
                'due_instalment': instalments,
                'emi_start_date': emi_start_date_str
            })

            LoanRepository.update(loan_id, update_dict, test=test)
            InstalmentRepository.delete_by_loan_id(loan_id, test=test)

            instalments_to_insert = []
            for i in range(1, instalments + 1):
                due_date = add_months(emi_start, i - 1)
                instalments_to_insert.append((
                    loan_id, float(instalment_amount), i, due_date.strftime('%Y-%m-%d')
                ))
            InstalmentRepository.create_many(instalments_to_insert, test=test)
        else:
            LoanRepository.update(loan_id, update_dict, test=test)

        return True, []

    @staticmethod
    def delete_loan(loan_id: int, test: bool = False) -> Tuple[bool, str]:
        collections_count = CollectionRepository.count_by_loan_id(loan_id, test=test)
        if collections_count > 0:
            return False, "This Client Instalment Paid."
        LoanRepository.delete(loan_id, test=test)
        InstalmentRepository.delete_by_loan_id(loan_id, test=test)
        return True, "Loan Delete Successfully."

    @staticmethod
    def close_loan(loan_id: int, due_amount: Decimal, payment_date: str, remark: str, test: bool = False) -> Tuple[bool, str]:
        loan = LoanRepository.get_by_id(loan_id, test=test)
        if not loan:
            return False, "Loan record not found."
        if int(loan.get('status', 1)) != 1:
            return False, "Unapprove Loan."
        
        current_due = Decimal(str(loan['due_amount']))
        if current_due < due_amount or current_due <= 0:
            return False, "Loan Amount Already Paid."

        today_str = date.today().strftime('%Y-%m-%d')
        pay_date_str = parse_date_str(payment_date)

        new_paid = Decimal(str(loan['paid_amount'])) + due_amount
        new_due = current_due - due_amount

        LoanRepository.update(loan_id, {
            'paid_amount': float(new_paid),
            'due_amount': float(new_due),
            'coll_date': today_str,
            'for_close': 'yes'
        }, test=test)

        CollectionRepository.create({
            'loan_id': loan_id,
            'instalment_amt': float(due_amount),
            'payment_date': pay_date_str,
            'remark': remark,
            'collect_date': today_str,
            'instal_no': 0
        }, test=test)

        return True, "Loan Close Successfully."
