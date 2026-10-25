import unittest
from decimal import Decimal
from services.loan_service import LoanService

class TestFinancialCalculations(unittest.TestCase):
    """Unit tests for loan interest, EMI schedule, and financial calculation workflows."""

    def test_installment_calculation(self):
        """Test calculation of monthly installment amount."""
        loan_interest_amount = Decimal('12000.00')
        tenure_months = 12
        installment_amt = LoanService.calculate_installment_amount(loan_interest_amount, tenure_months)
        self.assertEqual(installment_amt, Decimal('1000.00'))

    def test_installment_with_decimals(self):
        """Test calculation of installment with repeating decimals."""
        loan_interest_amount = Decimal('10000.00')
        tenure_months = 3
        installment_amt = LoanService.calculate_installment_amount(loan_interest_amount, tenure_months)
        self.assertEqual(installment_amt, Decimal('3333.33'))

    def test_installment_due_dates_progression(self):
        """Test monthly due dates progression from EMI start date."""
        start_date_str = "01-01-2023"
        due_dates = LoanService.calculate_due_dates(start_date_str, 3)
        self.assertEqual(len(due_dates), 3)
        self.assertEqual(due_dates[0], "2023-01-01")
        self.assertEqual(due_dates[1], "2023-02-01")
        self.assertEqual(due_dates[2], "2023-03-01")

    def test_loan_validation_success(self):
        """Test valid loan input."""
        valid_data = {
            'branch_id': '1',
            'client_name': 'Pradeep Dhangar',
            'father_name': 'Ram Dhangar',
            'city_village': 'Neemuch',
            'district': 'Neemuch',
            'mobile': '9876543210',
            'aadhar_no': '123456789012',
            'loan_amount': '10000.00',
            'loan_intrest_amount': '12000.00',
            'instalment': '12',
            'loan_application_date': '01-01-2023',
            'emi_start_date': '10-01-2023'
        }
        errors = LoanService.validate_loan_data(valid_data)
        self.assertEqual(len(errors), 0)

    def test_loan_validation_collective_amount_smaller(self):
        """Test that collective amount cannot be less than principal loan amount."""
        invalid_data = {
            'branch_id': '1',
            'client_name': 'Test Client',
            'father_name': 'Test Father',
            'city_village': 'Test City',
            'district': 'Test District',
            'mobile': '9876543210',
            'aadhar_no': '123456789012',
            'loan_amount': '10000.00',
            'loan_intrest_amount': '9000.00',  # Less than principal
            'instalment': '12',
            'loan_application_date': '01-01-2023',
            'emi_start_date': '10-01-2023'
        }
        errors = LoanService.validate_loan_data(invalid_data)
        self.assertTrue(any("less than the loan amount" in e for e in errors))

if __name__ == '__main__':
    unittest.main()
