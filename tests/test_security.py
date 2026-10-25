import unittest
import hashlib
from security import hash_password, verify_password, escape, SessionManager

class TestSecurity(unittest.TestCase):
    """Unit tests for password hashing, verification, session management, and escaping."""

    def test_pbkdf2_hash_and_verify(self):
        """Test PBKDF2 hashing and verification."""
        password = "admin_secure_password_123"
        hashed = hash_password(password)
        self.assertTrue(hashed.startswith("pbkdf2:sha256:"))
        self.assertTrue(verify_password(password, hashed))
        self.assertFalse(verify_password("wrong_password", hashed))

    def test_legacy_sha1_verification(self):
        """Test backward compatibility with CodeIgniter's legacy sha1 hashes."""
        password = "admin"
        legacy_hash = hashlib.sha1(password.encode('utf-8')).hexdigest()
        self.assertEqual(len(legacy_hash), 40)
        self.assertTrue(verify_password(password, legacy_hash))
        self.assertFalse(verify_password("wrong", legacy_hash))

    def test_html_escape(self):
        """Test escaping malicious script tags and HTML entities."""
        dangerous_input = '<script>alert("xss")</script> & "quotes"'
        safe_output = escape(dangerous_input)
        self.assertNotIn('<script>', safe_output)
        self.assertIn('&lt;script&gt;', safe_output)
        self.assertIn('&amp;', safe_output)
        self.assertIn('&quot;', safe_output)

    def test_session_lifecycle(self):
        """Test session creation, access, flash messages, and destruction."""
        mgr = SessionManager(expiry_seconds=10)
        user_info = {'user_id': 1, 'username': 'admin', 'email': 'admin@asthafinance.com'}
        
        session_id = mgr.create_session(user_info, is_app=False)
        self.assertIsNotNone(session_id)
        
        # Retrieve user
        retrieved_user = mgr.get_user(session_id, is_app=False)
        self.assertEqual(retrieved_user['email'], 'admin@asthafinance.com')

        # Flash messages
        mgr.set_flash(session_id, 'msg', 'Welcome Admin!')
        flash1 = mgr.get_flash(session_id, 'msg')
        self.assertEqual(flash1, 'Welcome Admin!')
        flash2 = mgr.get_flash(session_id, 'msg')
        self.assertIsNone(flash2)  # Should be cleared after first read

        # Destroy
        mgr.destroy_session(session_id, is_app=False)
        self.assertIsNone(mgr.get_user(session_id, is_app=False))

if __name__ == '__main__':
    unittest.main()
