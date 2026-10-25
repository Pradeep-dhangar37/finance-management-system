# Astha Finance Management System (Core Python & MySQL)

A complete, production-ready reimplementation of the Astha Finance Loan & Collection Management System built exclusively using **Core Python 3 Standard Library** (`http.server.ThreadingHTTPServer`) and **MySQL 8** (`mysql-connector-python`), with zero external web frameworks (no Flask, Django, FastAPI, SQLAlchemy, or React).

---

## 1. Project Overview & Architecture

This application reproduces the dual-portal financial management platform:
1. **Admin Management Portal (`/admin`)**:
   - Built with AdminLTE 2.4 and Bootstrap 3.
   - Comprehensive dashboard with aggregate metrics, charts, and financial KPIs.
   - Branch Management (Add & Edit branches).
   - Loan Management (Loan application creation, auto-generated application numbers, validation, approval/unapproval toggles, EMI installment schedules, editing, deletion rules, and early loan closure settlements).
   - Installment Collections (Daily EMI collection, customer installment breakdown, receipt printing, and installment payment deletion with balance rollback).
   - Reports (Ledger running balance, Outstanding client balances with Dr./Cr. indicator, Opening/Closing balance tracking, and Total balance disbursements).
   - Profile & Password Change.
2. **Mobile Agent Collection Portal (`/app`)**:
   - Specialized lightweight responsive interface for field collection agents.
   - Agent login, dashboard quick actions, customer collection receipt recording, today's collection, today's pending EMI list, customer details, installment breakdown, and thermal printer receipt invoice.

### Directory Structure

```
financemanagment/
├── app.py                      # Main entrypoint (http.server.ThreadingHTTPServer)
├── config.py                   # Configuration and environment variables (.env loader)
├── security.py                 # PBKDF2 hashing, legacy SHA1 compatibility, sessions, CSRF/escaping
├── db.py                       # MySQL connection pooling, transactions, parameterized queries
├── web.py                      # Request, Response, and URL router dispatch engine
├── template_engine.py          # Native lightweight template engine (filters, loops, includes)
├── requirements.txt            # Minimal third-party driver: mysql-connector-python
├── .env.example                # Environment variables template
├── .gitignore                  # Git ignore rules
├── README.md                   # Complete documentation
├── sql/
│   ├── schema.sql              # MySQL 8 DDL schema (tables, foreign keys, indexes, DECIMALs)
│   └── seed.sql                # Default initial seed data (admin & agent users, branches, sample data)
├── routes/
│   ├── auth_routes.py          # Admin & Mobile Agent login/logout and password change
│   ├── dashboard_routes.py     # Admin dashboard summaries and Total Due list
│   ├── branch_routes.py        # Branch CRUD operations
│   ├── loan_routes.py          # Loan lifecycle, validation, approval, close, installment schedules
│   ├── collection_routes.py    # Admin collection entry, receipt print, deletion rollback
│   ├── report_routes.py        # Financial Ledger, Outstanding, Opening/Closing, Total Balances
│   └── app_routes.py           # Mobile Agent portal workflows
├── services/
│   ├── loan_service.py         # Loan validation, EMI calculation, dates, settlement, deletion rules
│   ├── collection_service.py   # Collection processing, balance calculation, receipt generation
│   ├── dashboard_service.py    # Metric aggregation for dashboard cards and charts
│   ├── ledger_service.py       # Running balance calculation for ledger transactions
│   └── report_service.py       # Outstanding calculations with Dr./Cr. rules
├── repositories/
│   ├── user_repository.py      # Users table SQL operations
│   ├── branch_repository.py    # Branches table SQL operations
│   ├── loan_repository.py      # Loans table SQL queries and joins
│   ├── instalment_repository.py# Installments table SQL queries and batch operations
│   ├── collection_repository.py# Collections table SQL queries and receipt joins
│   └── report_repository.py    # Report tables and running balances
├── templates/
│   ├── admin/                  # 21 AdminLTE web views
│   └── app/                    # 10 Mobile agent views
├── static/
│   ├── assets/                 # AdminLTE, Bootstrap, Select2, FontAwesome, jQuery UI
│   └── img/                    # Logos and background assets
└── tests/
    ├── test_calculations.py    # Financial calculations and validation unit tests
    ├── test_security.py        # PBKDF2, legacy SHA1, session lifecycle tests
    ├── test_router.py          # Route matching, param extraction, method isolation tests
    ├── test_template_engine.py # Custom template engine tag, loop, and filter tests
    └── test_database.py        # Database connectivity and query tests
```

---

## 2. Quick Start & Setup Instructions

### Quick Start (If MySQL is already running)

```bash
# 1. Navigate to project directory
cd ~/Desktop/Developer/financemanagment

# 2. Activate virtual environment
source venv/bin/activate

# 3. Create database and load schema & seed data
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS asthafinance_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -u root -p asthafinance_db < sql/schema.sql
mysql -u root -p asthafinance_db < sql/seed.sql

# 4. Copy and verify .env configuration
cp .env.example .env
# Edit .env to set your DB_USER and DB_PASSWORD

# 5. Run the server
python app.py --port 8080
```

---

### Step-by-Step Installation Guide

Follow these step-by-step instructions to set up the application from scratch:

#### Step 1: Check Python Version
Ensure Python 3.10+ (tested on Python 3.13) is installed:
```bash
python3 --version
```

#### Step 2: Navigate to Destination Directory
```bash
cd ~/Desktop/Developer/financemanagment
```

#### Step 3: Create and Activate Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

#### Step 4: Install Dependencies
Install the single required MySQL database connector:
```bash
pip install -r requirements.txt
```

#### Step 5: Start MySQL Server
Start MySQL using Homebrew (or macOS MySQL service):
```bash
brew services start mysql
# Or if installed via macOS official installer:
# sudo /usr/local/mysql/support-files/mysql.server start
```

#### Step 6: Create Database & User
Log into MySQL:
```bash
mysql -u root -p
```
Run the following SQL commands to create the database:
```sql
CREATE DATABASE IF NOT EXISTS asthafinance_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

*(Optional) Create a dedicated user:*
```sql
CREATE USER IF NOT EXISTS 'astha_user'@'localhost' IDENTIFIED BY 'AsthaSecurePass2026!';
GRANT ALL PRIVILEGES ON asthafinance_db.* TO 'astha_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

#### Step 7: Import Schema and Seed Data
Execute the database schema and default initial seed data into `asthafinance_db`:
```bash
mysql -u root -p asthafinance_db < sql/schema.sql
mysql -u root -p asthafinance_db < sql/seed.sql
```

#### Step 8: Configure Environment Variables (.env)
Create your `.env` configuration:
```bash
cp .env.example .env
```
Ensure `.env` contains your correct database credentials:
```ini
# Database Configuration
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=asthafinance_db
DB_USER=root
DB_PASSWORD=your_mysql_password

# Test Database Configuration
TEST_DB_NAME=asthafinance_db
TEST_DB_USER=root
TEST_DB_PASSWORD=your_mysql_password

# Application Server Configuration
HOST=127.0.0.1
PORT=8080
SECRET_KEY=change_me_to_a_random_secure_secret_key_32_chars
DEBUG=True
```

---

## 3. Running the Application

Start the server using Python standard library:
```bash
source venv/bin/activate
python app.py
```
You can also specify a custom port or host:
```bash
python app.py --port 8080 --host 127.0.0.1
```

---

## 4. Accessing the Application

Open your web browser:
- **Admin Management Portal:** `http://127.0.0.1:8080/admin/login`
- **Mobile Agent Collection Portal:** `http://127.0.0.1:8080/app/login`
- **Default Seed Accounts:**
  - **Admin Login:**
    - Email: `admin@asthafinance.com` (or `admin@gmail.com`)
    - Password: `admin123`
  - **Agent Login:**
    - Email: `agent@asthafinance.com`
    - Password: `admin123`

---

## 5. Running the Automated Test Suite

Run the built-in `unittest` test suite without third-party test runners:
```bash
source venv/bin/activate
python -m unittest discover -s tests -v
```

All 22 unit tests verify:
- Financial EMI and interest calculations (`loan_intrest_amount / instalment`).
- Progressive monthly due date calculation.
- Loan validation rules (principal vs collective amount).
- PBKDF2 password hashing with cryptographically secure salts.
- Legacy SHA1 verification backward compatibility.
- In-memory session lifecycle and one-time flash messages.
- XSS HTML entity escaping.
- URL parameterized route matching and HTTP method isolation.
- Template rendering (loops, conditionals, filters).
- Database connectivity and ping.

---

## 6. Key Business Logic & Calculations Preserved

1. **Loan Collective Amount:**
   - `loan_intrest_amount` represents the Total Collective Amount (Principal + Interest).
   - The application strictly enforces `loan_intrest_amount >= loan_amount`.
2. **EMI Installment Calculation:**
   - `instalment_amount = round(loan_intrest_amount / instalment, 2)`
   - Scheduled installment due dates are generated month-by-month starting from `emi_start_date`.
3. **Delete Loan Protection:**
   - Loans cannot be deleted if any installments have already been collected (`del_loan == 'Yes'` rule).
4. **Installment Deletion & Reversal:**
   - Deleting a recorded installment safely rolls back the loan `paid_amount` and `due_amount` and marks the specific installment in `instalment_tbl` back to `unpaid`.
5. **Loan Close Workflow:**
   - Setting `for_close = 'yes'`, setting `due_amount = 0`, adding remaining due to `paid_amount`, and recording a final settlement collection entry.
6. **Outstanding Report Calculation:**
   - Outstanding balances are computed from total collective amounts minus recorded deposits, indicating Debit / Credit balances.
