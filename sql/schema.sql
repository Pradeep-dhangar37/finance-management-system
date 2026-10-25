-- ============================================================
-- Finance Management Database Schema (MySQL 8.0+)
-- Reproduction of Astha Finance Management System
-- ============================================================

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS `collection_tbl`;
DROP TABLE IF EXISTS `instalment_tbl`;
DROP TABLE IF EXISTS `loan_tbl`;
DROP TABLE IF EXISTS `branch_tbl`;
DROP TABLE IF EXISTS `users_tbl`;
DROP TABLE IF EXISTS `opclosingbalrep_tbl`;
DROP TABLE IF EXISTS `reportstotal_tbl`;
SET FOREIGN_KEY_CHECKS = 1;

-- ------------------------------------------------------------
-- Table: users_tbl (System Users / Admins / Agents)
-- ------------------------------------------------------------
CREATE TABLE `users_tbl` (
    `user_id` INT AUTO_INCREMENT PRIMARY KEY,
    `username` VARCHAR(100) NOT NULL,
    `email` VARCHAR(191) NOT NULL UNIQUE,
    `password` VARCHAR(255) NOT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- Table: branch_tbl (Company Branches)
-- ------------------------------------------------------------
CREATE TABLE `branch_tbl` (
    `branch_id` INT AUTO_INCREMENT PRIMARY KEY,
    `branch_name` VARCHAR(191) NOT NULL UNIQUE,
    `ad_date` DATE NOT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_branch_name` (`branch_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- Table: loan_tbl (Loan Applications & Details)
-- ------------------------------------------------------------
CREATE TABLE `loan_tbl` (
    `loan_id` INT AUTO_INCREMENT PRIMARY KEY,
    `branch_id` INT NOT NULL,
    `client_name` VARCHAR(150) NOT NULL,
    `father_name` VARCHAR(150) NOT NULL,
    `city_village` VARCHAR(150) NOT NULL,
    `district` VARCHAR(100) NOT NULL,
    `mobile` VARCHAR(15) NOT NULL,
    `aadhar_no` VARCHAR(20) NOT NULL,
    `loan_application_no` VARCHAR(50) NOT NULL UNIQUE,
    `loan_application_date` DATE NOT NULL,
    `loan_amount` DECIMAL(12, 2) NOT NULL,
    `loan_intrest_amount` DECIMAL(12, 2) NOT NULL,
    `instalment` INT NOT NULL,
    `instalment_amount` DECIMAL(12, 2) NOT NULL,
    `paid_amount` DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    `due_amount` DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    `paid_instalment` INT NOT NULL DEFAULT 0,
    `due_instalment` INT NOT NULL DEFAULT 0,
    `emi_start_date` DATE NOT NULL,
    `status` TINYINT NOT NULL DEFAULT 1,
    `for_close` VARCHAR(10) NOT NULL DEFAULT 'no',
    `coll_date` DATE DEFAULT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_branch_id` (`branch_id`),
    INDEX `idx_app_no` (`loan_application_no`),
    INDEX `idx_client_name` (`client_name`),
    INDEX `idx_due_amount` (`due_amount`),
    INDEX `idx_loan_status` (`status`, `for_close`),
    CONSTRAINT `fk_loan_branch` FOREIGN KEY (`branch_id`)
        REFERENCES `branch_tbl` (`branch_id`)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- Table: instalment_tbl (Scheduled EMI Instalments)
-- ------------------------------------------------------------
CREATE TABLE `instalment_tbl` (
    `ins_id` INT AUTO_INCREMENT PRIMARY KEY,
    `loan_id` INT NOT NULL,
    `instalment_no` INT NOT NULL,
    `instalment_amt` DECIMAL(12, 2) NOT NULL,
    `due_date` DATE NOT NULL,
    `collect_date` DATE DEFAULT NULL,
    `status` VARCHAR(20) NOT NULL DEFAULT 'unpaid',
    INDEX `idx_loan_id` (`loan_id`),
    INDEX `idx_due_date_status` (`due_date`, `status`),
    INDEX `idx_loan_inst` (`loan_id`, `instalment_no`),
    CONSTRAINT `fk_instalment_loan` FOREIGN KEY (`loan_id`)
        REFERENCES `loan_tbl` (`loan_id`)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- Table: collection_tbl (Recorded Payments & Collections)
-- ------------------------------------------------------------
CREATE TABLE `collection_tbl` (
    `collection_id` INT AUTO_INCREMENT PRIMARY KEY,
    `loan_id` INT NOT NULL,
    `instalment_amt` DECIMAL(12, 2) NOT NULL,
    `payment_date` DATE NOT NULL,
    `remark` TEXT NULL,
    `collect_date` DATE NOT NULL,
    `instal_no` INT NOT NULL,
    `created` DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_coll_loan` (`loan_id`),
    INDEX `idx_coll_date` (`collect_date`),
    INDEX `idx_pay_date` (`payment_date`),
    CONSTRAINT `fk_collection_loan` FOREIGN KEY (`loan_id`)
        REFERENCES `loan_tbl` (`loan_id`)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- Table: opclosingbalrep_tbl (Report 2: Opening/Closing Balance)
-- ------------------------------------------------------------
CREATE TABLE `opclosingbalrep_tbl` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `opening_bal` DECIMAL(12, 2) NOT NULL,
    `total_collection` DECIMAL(12, 2) NOT NULL,
    `closing_bal` DECIMAL(12, 2) NOT NULL,
    `rdpayment` DECIMAL(12, 2) NOT NULL,
    `total_bal` DECIMAL(12, 2) NOT NULL,
    `ad_date` DATE NOT NULL,
    INDEX `idx_ad_date` (`ad_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- Table: reportstotal_tbl (Report 3: Total Balance & Disbursements)
-- ------------------------------------------------------------
CREATE TABLE `reportstotal_tbl` (
    `rid` INT AUTO_INCREMENT PRIMARY KEY,
    `total_disabesment` DECIMAL(12, 2) NOT NULL,
    `current_outstanding` DECIMAL(12, 2) NOT NULL,
    `difference_outstanding` DECIMAL(12, 2) NOT NULL,
    `client_disabsment` DECIMAL(12, 2) NOT NULL,
    `interest_amount` DECIMAL(12, 2) NOT NULL,
    `ad_date` DATE NOT NULL,
    INDEX `idx_rep_ad_date` (`ad_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
