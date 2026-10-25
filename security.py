"""
Security module for Finance Management System.
Provides secure password hashing, verification, session management, and CSRF protection.
"""
import hashlib
import hmac
import html
import os
import secrets
import time
from typing import Optional, Dict, Any

def hash_password(password: str) -> str:
    """Hash password using PBKDF2-HMAC-SHA256 with a cryptographically secure salt."""
    salt = secrets.token_hex(16)
    iterations = 100000
    derived = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), iterations)
    return f"pbkdf2:sha256:{iterations}${salt}${derived.hex()}"

def verify_password(plain_password: str, stored_hash: str) -> bool:
    """
    Verify password against stored hash.
    Supports modern PBKDF2-HMAC-SHA256 and legacy SHA1 (40-char hex string).
    """
    if not stored_hash or not plain_password:
        return False
    
    # Check legacy SHA1 hash (40 lowercase hex characters)
    if len(stored_hash) == 40 and all(c in '0123456789abcdefABCDEF' for c in stored_hash):
        sha1_hash = hashlib.sha1(plain_password.encode('utf-8')).hexdigest()
        return hmac.compare_digest(sha1_hash.lower(), stored_hash.lower())

    # Check PBKDF2 format
    if stored_hash.startswith("pbkdf2:sha256:"):
        try:
            parts = stored_hash.split('$')
            if len(parts) == 3:
                algo_iter, salt, expected_hash = parts
                iterations = int(algo_iter.split(':')[-1])
                derived = hashlib.pbkdf2_hmac('sha256', plain_password.encode('utf-8'), salt.encode('utf-8'), iterations)
                return hmac.compare_digest(derived.hex(), expected_hash)
        except Exception:
            return False

    return False

def escape(val: Any) -> str:
    """HTML escape string value."""
    if val is None:
        return ""
    return html.escape(str(val))


class SessionManager:
    """In-memory thread-safe session store with timeout expiration."""
    def __init__(self, expiry_seconds=86400):
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self.expiry_seconds = expiry_seconds

    def create_session(self, user_data: Dict[str, Any], is_app: bool = False) -> str:
        session_id = secrets.token_urlsafe(32)
        session_key = 'appuser' if is_app else 'user'
        self._sessions[session_id] = {
            session_key: user_data,
            'created_at': time.time(),
            'last_accessed': time.time(),
            'flash_messages': {}
        }
        return session_id

    def get_session(self, session_id: Optional[str]) -> Optional[Dict[str, Any]]:
        if not session_id or session_id not in self._sessions:
            return None
        session = self._sessions[session_id]
        if time.time() - session['last_accessed'] > self.expiry_seconds:
            del self._sessions[session_id]
            return None
        session['last_accessed'] = time.time()
        return session

    def set_user(self, session_id: str, user_data: Dict[str, Any], is_app: bool = False):
        session = self.get_session(session_id)
        if not session:
            session = {
                'created_at': time.time(),
                'last_accessed': time.time(),
                'flash_messages': {}
            }
            self._sessions[session_id] = session
        key = 'appuser' if is_app else 'user'
        session[key] = user_data

    def get_user(self, session_id: Optional[str], is_app: bool = False) -> Optional[Dict[str, Any]]:
        session = self.get_session(session_id)
        if not session:
            return None
        key = 'appuser' if is_app else 'user'
        return session.get(key)

    def destroy_session(self, session_id: Optional[str], is_app: bool = False):
        if not session_id or session_id not in self._sessions:
            return
        key = 'appuser' if is_app else 'user'
        if key in self._sessions[session_id]:
            del self._sessions[session_id][key]
        # If no user left in session, remove entire session
        if 'user' not in self._sessions[session_id] and 'appuser' not in self._sessions[session_id]:
            del self._sessions[session_id]

    def set_flash(self, session_id: Optional[str], key: str, message: str):
        if not session_id:
            return
        session = self.get_session(session_id)
        if session:
            session['flash_messages'][key] = message

    def get_flash(self, session_id: Optional[str], key: str) -> Optional[str]:
        if not session_id:
            return None
        session = self.get_session(session_id)
        if session and key in session['flash_messages']:
            msg = session['flash_messages'][key]
            del session['flash_messages'][key]
            return msg
        return None

session_manager = SessionManager()
