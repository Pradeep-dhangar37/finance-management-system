"""
Configuration module for Finance Management System.
Loads settings from .env file or environment variables without third-party dependencies.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def load_env_file(env_path=None):
    """Parse .env file into os.environ if it exists."""
    if env_path is None:
        env_path = BASE_DIR / '.env'
    if not os.path.exists(env_path):
        return
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, val = line.split('=', 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key not in os.environ:
                os.environ[key] = val

load_env_file()

class Config:
    # Database Settings
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = int(os.environ.get('DB_PORT', 3306))
    DB_NAME = os.environ.get('DB_NAME', 'asthafinance_db')
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')

    # Test Database Settings
    TEST_DB_NAME = os.environ.get('TEST_DB_NAME', 'financemanagement_test_db')
    TEST_DB_USER = os.environ.get('TEST_DB_USER', DB_USER)
    TEST_DB_PASSWORD = os.environ.get('TEST_DB_PASSWORD', DB_PASSWORD)

    # Server Settings
    HOST = os.environ.get('HOST', '127.0.0.1')
    PORT = int(os.environ.get('PORT', 8080))
    DEBUG = os.environ.get('DEBUG', 'True').lower() in ('true', '1', 'yes')

    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default_secret_key_change_in_production_123456')
    SESSION_COOKIE_NAME = 'finance_session_id'
    SESSION_EXPIRY_SECONDS = 86400  # 24 hours

    # Paths
    BASE_DIR = BASE_DIR
    TEMPLATES_DIR = BASE_DIR / 'templates'
    STATIC_DIR = BASE_DIR / 'static'
    SQL_DIR = BASE_DIR / 'sql'

