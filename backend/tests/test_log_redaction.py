"""
Unit Tests for Sensitive Data Filter

Tests the log redaction filter to ensure sensitive information
(emails, passwords, tokens, etc.) is properly redacted from logs.

Run: python -m pytest tests/test_log_redaction.py -v
"""

import os
import sys
import unittest
import logging
from io import StringIO
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_dir))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'verfai.settings')

from src.infrastructure.logging.sensitive_filter import SensitiveDataFilter, redact_sensitive_data


class TestSensitiveDataFilter(unittest.TestCase):
    """Test the SensitiveDataFilter for log redaction."""
    
    def setUp(self):
        """Set up test logger with filter."""
        self.filter = SensitiveDataFilter()
        
        # Create test logger
        self.logger = logging.getLogger('test_redaction')
        self.logger.setLevel(logging.INFO)
        
        # Clear existing handlers
        self.logger.handlers = []
        
        # Add string stream handler for testing
        self.log_stream = StringIO()
        handler = logging.StreamHandler(self.log_stream)
        handler.addFilter(self.filter)
        self.logger.addHandler(handler)
    
    def get_log_output(self) -> str:
        """Get the current log output."""
        return self.log_stream.getvalue()
    
    def test_email_redacted(self):
        """Test that email addresses are redacted."""
        self.logger.info("User test@example.com logged in")
        output = self.get_log_output()
        
        self.assertNotIn("test@example.com", output)
        self.assertIn("***EMAIL_REDACTED***", output)
    
    def test_multiple_emails_redacted(self):
        """Test that multiple emails in one message are redacted."""
        self.logger.info("Sent from admin@verif-ai.com to user@test.org")
        output = self.get_log_output()
        
        self.assertNotIn("admin@verif-ai.com", output)
        self.assertNotIn("user@test.org", output)
        self.assertEqual(output.count("***EMAIL_REDACTED***"), 2)
    
    def test_password_colon_format_redacted(self):
        """Test password in 'password: value' format."""
        self.logger.info('User credentials: password: "secret123"')
        output = self.get_log_output()
        
        self.assertNotIn("secret123", output)
        self.assertIn("***REDACTED***", output)
    
    def test_password_equals_format_redacted(self):
        """Test password in 'password=value' format."""
        self.logger.info("Reset password=MyP@ssw0rd for user")
        output = self.get_log_output()
        
        self.assertNotIn("MyP@ssw0rd", output)
        self.assertIn("***REDACTED***", output)
    
    def test_password_json_format_redacted(self):
        """Test password in JSON format."""
        self.logger.info('{"username": "admin", "password": "admin123"}')
        output = self.get_log_output()
        
        self.assertNotIn("admin123", output)
        self.assertIn("***REDACTED***", output)
    
    def test_bearer_token_redacted(self):
        """Test JWT bearer tokens are redacted."""
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
        self.logger.info(f"Authorization: Bearer {token}")
        output = self.get_log_output()
        
        self.assertNotIn(token, output)
        self.assertIn("Bearer ***TOKEN_REDACTED***", output)
    
    def test_api_key_redacted(self):
        """Test API keys are redacted."""
        self.logger.info("api_key: EXAMPLE_API_KEY_1234567890abcdefghijklmnop")
        output = self.get_log_output()
        
        self.assertNotIn("EXAMPLE_API_KEY_1234567890abcdefghijklmnop", output)
        self.assertIn("***REDACTED***", output)
    
    def test_mongodb_uri_redacted(self):
        """Test MongoDB connection strings with credentials are redacted."""
        uri = "mongodb://username:password@cluster0.mongodb.net/mydb"
        self.logger.info(f"Connecting to: {uri}")
        output = self.get_log_output()
        
        self.assertNotIn("username:password", output)
        self.assertIn("***REDACTED***:***REDACTED***@", output)
    
    def test_mongodb_srv_uri_redacted(self):
        """Test MongoDB+srv connection strings are redacted."""
        uri = "mongodb+srv://admin:secretpass@cluster.mongodb.net/"
        self.logger.info(f"Database URI: {uri}")
        output = self.get_log_output()
        
        self.assertNotIn("admin:secretpass", output)
        self.assertIn("***REDACTED***:***REDACTED***@", output)
    
    def test_private_key_redacted(self):
        """Test blockchain private keys are redacted."""
        self.logger.info("private_key: 0x1234567890abcdef1234567890abcdef1234567890abcdef")
        output = self.get_log_output()
        
        self.assertNotIn("0x1234567890abcdef", output)
        self.assertIn("***REDACTED***", output)
    
    def test_session_token_redacted(self):
        """Test session tokens are redacted."""
        self.logger.info("session_token=abc123def456ghi789jkl012mno345pqr678")
        output = self.get_log_output()
        
        self.assertNotIn("abc123def456ghi789jkl012mno345pqr678", output)
        self.assertIn("***REDACTED***", output)
    
    def test_credit_card_redacted(self):
        """Test credit card numbers are redacted."""
        self.logger.info("Payment processed: 4532-1234-5678-9010")
        output = self.get_log_output()
        
        self.assertNotIn("4532-1234-5678-9010", output)
        self.assertIn("***CARD_REDACTED***", output)
    
    def test_phone_number_redacted(self):
        """Test international phone numbers are redacted."""
        self.logger.info("Contact: +1 (555) 123-4567")
        output = self.get_log_output()
        
        self.assertNotIn("+1 (555) 123-4567", output)
        self.assertIn("***PHONE_REDACTED***", output)
    
    def test_ssn_redacted(self):
        """Test Social Security Numbers are redacted."""
        self.logger.info("SSN: 123-45-6789")
        output = self.get_log_output()
        
        self.assertNotIn("123-45-6789", output)
        self.assertIn("***SSN_REDACTED***", output)
    
    def test_multiple_sensitive_items_redacted(self):
        """Test multiple types of sensitive data in one message."""
        msg = "User admin@test.com with password=secret123 and token Bearer xyz789"
        self.logger.info(msg)
        output = self.get_log_output()
        
        self.assertNotIn("admin@test.com", output)
        self.assertNotIn("secret123", output)
        self.assertNotIn("xyz789", output)
        self.assertIn("***EMAIL_REDACTED***", output)
        self.assertIn("***REDACTED***", output)
        self.assertIn("***TOKEN_REDACTED***", output)
    
    def test_non_sensitive_data_not_redacted(self):
        """Test that non-sensitive data is not modified."""
        msg = "User logged in successfully from IP 192.168.1.1"
        self.logger.info(msg)
        output = self.get_log_output()
        
        self.assertIn("User logged in successfully", output)
        self.assertIn("192.168.1.1", output)
    
    def test_case_insensitive_redaction(self):
        """Test that redaction is case-insensitive."""
        self.logger.info("PASSWORD: Secret123")
        self.logger.info("Password: Secret456")
        self.logger.info("password: Secret789")
        output = self.get_log_output()
        
        self.assertNotIn("Secret123", output)
        self.assertNotIn("Secret456", output)
        self.assertNotIn("Secret789", output)


class TestRedactDictFunction(unittest.TestCase):
    """Test the redact_dict helper function."""
    
    def test_redact_sensitive_keys(self):
        """Test redacting sensitive dictionary keys."""
        data = {
            "username": "admin",
            "password": "secret123",
            "email": "test@example.com",
            "public_field": "safe_value"
        }
        
        redacted = SensitiveDataFilter.redact_dict(data)
        
        self.assertEqual(redacted["username"], "admin")  # Not sensitive
        self.assertEqual(redacted["password"], "***REDACTED***")
        self.assertEqual(redacted["email"], "***REDACTED***")
        self.assertEqual(redacted["public_field"], "safe_value")
    
    def test_redact_nested_dict(self):
        """Test redacting nested dictionaries."""
        data = {
            "user": {
                "name": "John",
                "password": "secret",
                "api_key": "key123"
            },
            "config": {
                "debug": True,
                "secret_key": "django-secret"
            }
        }
        
        redacted = SensitiveDataFilter.redact_dict(data)
        
        self.assertEqual(redacted["user"]["name"], "John")
        self.assertEqual(redacted["user"]["password"], "***REDACTED***")
        self.assertEqual(redacted["user"]["api_key"], "***REDACTED***")
        self.assertEqual(redacted["config"]["secret_key"], "***REDACTED***")
    
    def test_redact_list_of_dicts(self):
        """Test redacting lists containing dictionaries."""
        data = {
            "users": [
                {"name": "Alice", "password": "pass1"},
                {"name": "Bob", "password": "pass2"}
            ]
        }
        
        redacted = SensitiveDataFilter.redact_dict(data)
        
        self.assertEqual(redacted["users"][0]["name"], "Alice")
        self.assertEqual(redacted["users"][0]["password"], "***REDACTED***")
        self.assertEqual(redacted["users"][1]["password"], "***REDACTED***")
    
    def test_custom_sensitive_keys(self):
        """Test redacting with custom sensitive keys list."""
        data = {
            "api_token": "token123",
            "internal_id": "secret456",
            "public_data": "visible"
        }
        
        redacted = SensitiveDataFilter.redact_dict(
            data,
            sensitive_keys=["api_token", "internal_id"]
        )
        
        self.assertEqual(redacted["api_token"], "***REDACTED***")
        self.assertEqual(redacted["internal_id"], "***REDACTED***")
        self.assertEqual(redacted["public_data"], "visible")


class TestManualRedactionFunction(unittest.TestCase):
    """Test the manual redact_sensitive_data function."""
    
    def test_manual_email_redaction(self):
        """Test manually redacting email from a string."""
        text = "Contact us at support@verif-ai.com for help"
        redacted = redact_sensitive_data(text)
        
        self.assertNotIn("support@verif-ai.com", redacted)
        self.assertIn("***EMAIL_REDACTED***", redacted)
    
    def test_manual_password_redaction(self):
        """Test manually redacting password from a string."""
        text = 'Login failed: {"username": "admin", "password": "wrong"}'
        redacted = redact_sensitive_data(text)
        
        self.assertNotIn('"password": "wrong"', redacted)
        self.assertIn("***REDACTED***", redacted)
    
    def test_manual_combined_redaction(self):
        """Test manually redacting multiple sensitive items."""
        text = "User admin@test.com with API key api_key=sk_12345678901234567890"
        redacted = redact_sensitive_data(text)
        
        self.assertNotIn("admin@test.com", redacted)
        self.assertNotIn("sk_12345678901234567890", redacted)
        self.assertIn("***EMAIL_REDACTED***", redacted)
        self.assertIn("***REDACTED***", redacted)


if __name__ == '__main__':
    unittest.main()
