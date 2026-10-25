-- ============================================================
-- Seed Data for Finance Management System
-- ============================================================

-- Default Users (Password is 'admin123' -> SHA1: f865b53623b121fd34ee5426c792e5c33af8c227)
INSERT INTO `users_tbl` (`user_id`, `username`, `email`, `password`, `created_at`) VALUES
(1, 'Admin', 'admin@asthafinance.com', 'f865b53623b121fd34ee5426c792e5c33af8c227', NOW()),
(2, 'Administrator', 'admin@gmail.com', 'f865b53623b121fd34ee5426c792e5c33af8c227', NOW()),
(3, 'Collection Agent', 'agent@asthafinance.com', 'f865b53623b121fd34ee5426c792e5c33af8c227', NOW())
ON DUPLICATE KEY UPDATE `username`=VALUES(`username`);

-- Sample Branches
INSERT INTO `branch_tbl` (`branch_id`, `branch_name`, `ad_date`, `created_at`) VALUES
(1, 'Neemuch Main Branch', CURDATE(), NOW()),
(2, 'Rampura Branch', CURDATE(), NOW()),
(3, 'Manasa Branch', CURDATE(), NOW())
ON DUPLICATE KEY UPDATE `branch_name`=VALUES(`branch_name`);

-- Sample Loan 1: Rajesh Sharma, 10-month loan of 50,000 principal, 60,000 collective
INSERT INTO `loan_tbl` (
    `loan_id`, `branch_id`, `client_name`, `father_name`, `city_village`, `district`,
    `mobile`, `aadhar_no`, `loan_application_no`, `loan_application_date`,
    `loan_amount`, `loan_intrest_amount`, `instalment`, `instalment_amount`,
    `paid_amount`, `due_amount`, `paid_instalment`, `due_instalment`,
    `emi_start_date`, `status`, `for_close`, `coll_date`, `created_at`
) VALUES (
    1, 1, 'Rajesh Sharma', 'Ramesh Sharma', 'Neemuch City', 'Neemuch',
    '9876543210', '123456789012', '1001', '2026-01-10',
    50000.00, 60000.00, 10, 6000.00,
    12000.00, 48000.00, 2, 8,
    '2026-02-10', 1, 'no', CURDATE(), NOW()
) ON DUPLICATE KEY UPDATE `loan_id`=`loan_id`;

-- Instalments for Loan 1
INSERT INTO `instalment_tbl` (`ins_id`, `loan_id`, `instalment_no`, `instalment_amt`, `due_date`, `collect_date`, `status`) VALUES
(1, 1, 1, 6000.00, '2026-02-10', '2026-02-10', 'paid'),
(2, 1, 2, 6000.00, '2026-03-10', '2026-03-10', 'paid'),
(3, 1, 3, 6000.00, '2026-04-10', NULL, 'unpaid'),
(4, 1, 4, 6000.00, '2026-05-10', NULL, 'unpaid'),
(5, 1, 5, 6000.00, '2026-06-10', NULL, 'unpaid'),
(6, 1, 6, 6000.00, '2026-07-10', NULL, 'unpaid'),
(7, 1, 7, 6000.00, '2026-08-10', NULL, 'unpaid'),
(8, 1, 8, 6000.00, '2026-09-10', NULL, 'unpaid'),
(9, 1, 9, 6000.00, '2026-10-10', NULL, 'unpaid'),
(10, 1, 10, 6000.00, '2026-11-10', NULL, 'unpaid')
ON DUPLICATE KEY UPDATE `ins_id`=`ins_id`;

-- Collections for Loan 1
INSERT INTO `collection_tbl` (`collection_id`, `loan_id`, `instalment_amt`, `payment_date`, `remark`, `collect_date`, `instal_no`, `created`) VALUES
(1, 1, 6000.00, '2026-02-10', 'First instalment paid in cash', '2026-02-10', 1, NOW()),
(2, 1, 6000.00, '2026-03-10', 'Second instalment paid via UPI', '2026-03-10', 2, NOW())
ON DUPLICATE KEY UPDATE `collection_id`=`collection_id`;

-- Sample Report 2 (Opening/Closing Balance)
INSERT INTO `opclosingbalrep_tbl` (`id`, `opening_bal`, `total_collection`, `closing_bal`, `rdpayment`, `total_bal`, `ad_date`) VALUES
(1, 250000.00, 48000.00, 298000.00, 12000.00, 310000.00, CURDATE())
ON DUPLICATE KEY UPDATE `id`=`id`;

-- Sample Report 3 (Total Balance & Disbursement)
INSERT INTO `reportstotal_tbl` (`rid`, `total_disabesment`, `current_outstanding`, `difference_outstanding`, `client_disabsment`, `interest_amount`, `ad_date`) VALUES
(1, 500000.00, 380000.00, 120000.00, 10.00, 75000.00, CURDATE())
ON DUPLICATE KEY UPDATE `rid`=`rid`;
