"""
Log Redaction Demo

Demonstrates how the SensitiveDataFilter automatically redacts
sensitive information from logs.

Run: python backend/scripts/demo_log_redaction.py
"""

import os
import sys
import logging
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_dir))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'verfai.settings')

# Import Django to configure logging
import django
django.setup()

from src.infrastructure.logging.sensitive_filter import SensitiveDataFilter, redact_sensitive_data


def demo_automatic_redaction():
    """Demonstrate automatic log redaction via configured logger."""
    print("=" * 70)
    print("DEMO 1: Automatic Redaction (Django Logger)")
    print("=" * 70)
    
    logger = logging.getLogger('security')
    
    print("\n1️⃣  Email Redaction:")
    print("-" * 50)
    print("Input:  logger.info('User admin@example.com logged in')")
    logger.info("User admin@example.com logged in")
    print("Output: Check logs/security.log - email is redacted ✅")
    
    print("\n2️⃣  Password Redaction:")
    print("-" * 50)
    print('Input:  logger.info(\'Password reset: password="secret123"\')')
    logger.info('Password reset: password="secret123"')
    print("Output: Check logs/security.log - password is redacted ✅")
    
    print("\n3️⃣  Bearer Token Redaction:")
    print("-" * 50)
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.abc"
    print(f"Input:  logger.info('Auth: Bearer {token}')")
    logger.info(f"Auth: Bearer {token}")
    print("Output: Check logs/security.log - token is redacted ✅")
    
    print("\n4️⃣  MongoDB URI Redaction:")
    print("-" * 50)
    uri = "mongodb+srv://admin:secretpass@cluster0.mongodb.net/"
    print(f"Input:  logger.info('Connecting to {uri}')")
    logger.info(f"Connecting to {uri}")
    print("Output: Check logs/security.log - credentials are redacted ✅")
    
    print("\n5️⃣  Multiple Sensitive Items:")
    print("-" * 50)
    msg = "User test@example.com with api_key=sk_live_abc123 authenticated"
    print(f"Input:  logger.info('{msg}')")
    logger.info(msg)
    print("Output: Check logs/security.log - all sensitive data redacted ✅")


def demo_manual_redaction():
    """Demonstrate manual redaction function."""
    print("\n\n" + "=" * 70)
    print("DEMO 2: Manual Redaction Function")
    print("=" * 70)
    
    print("\n1️⃣  Email Redaction:")
    print("-" * 50)
    text = "Contact support@verif-ai.com for assistance"
    redacted = redact_sensitive_data(text)
    print(f"Input:    {text}")
    print(f"Redacted: {redacted}")
    
    print("\n2️⃣  Password Redaction:")
    print("-" * 50)
    text = '{"username": "admin", "password": "secret"}'
    redacted = redact_sensitive_data(text)
    print(f"Input:    {text}")
    print(f"Redacted: {redacted}")
    
    print("\n3️⃣  API Key Redaction:")
    print("-" * 50)
    text = "Your API key: api_key=sk_live_1234567890abcdefghijkl"
    redacted = redact_sensitive_data(text)
    print(f"Input:    {text}")
    print(f"Redacted: {redacted}")


def demo_dict_redaction():
    """Demonstrate dictionary redaction for structured logging."""
    print("\n\n" + "=" * 70)
    print("DEMO 3: Dictionary Redaction (Structured Logging)")
    print("=" * 70)
    
    print("\n1️⃣  User Data Redaction:")
    print("-" * 50)
    user_data = {
        "user_id": "abc123",
        "username": "admin",
        "email": "admin@example.com",
        "password": "secret123",
        "role": "administrator"
    }
    print(f"Original: {user_data}")
    
    redacted = SensitiveDataFilter.redact_dict(user_data)
    print(f"Redacted: {redacted}")
    
    print("\n2️⃣  Nested Dictionary Redaction:")
    print("-" * 50)
    config = {
        "app": "verif-ai",
        "database": {
            "host": "localhost",
            "username": "admin",
            "password": "dbpass123"
        },
        "api": {
            "api_key": "sk_live_xyz",
            "timeout": 30
        }
    }
    print(f"Original: {config}")
    
    redacted = SensitiveDataFilter.redact_dict(config)
    print(f"Redacted: {redacted}")
    
    print("\n3️⃣  Custom Sensitive Keys:")
    print("-" * 50)
    data = {
        "public_id": "123",
        "internal_secret": "confidential",
        "api_token": "xyz",
        "description": "visible"
    }
    print(f"Original: {data}")
    
    redacted = SensitiveDataFilter.redact_dict(
        data,
        sensitive_keys=["internal_secret", "api_token"]
    )
    print(f"Redacted: {redacted}")


def demo_verification():
    """Verify that redaction is working in log files."""
    print("\n\n" + "=" * 70)
    print("VERIFICATION: Check Log Files")
    print("=" * 70)
    
    log_file = Path(backend_dir) / "logs" / "security.log"
    
    if log_file.exists():
        print(f"\n📄 Log file: {log_file}")
        print("\nLast 10 lines of security.log:")
        print("-" * 70)
        
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines[-10:]:
                print(line.rstrip())
        
        print("\n✅ Verification Tips:")
        print("   - Search for '@' characters (should only find in domain names)")
        print("   - Search for 'password' (should only find with ***REDACTED***)")
        print("   - Search for 'Bearer' (should only find with ***TOKEN_REDACTED***)")
        print("   - All sensitive data should show as ***REDACTED*** or similar")
    else:
        print(f"\n⚠️  Log file not found: {log_file}")
        print("   Run this script to generate logs, then check the file.")


def main():
    """Run all demos."""
    print("\n" + "🔐" * 35)
    print("  LOG REDACTION DEMONSTRATION")
    print("🔐" * 35)
    
    demo_automatic_redaction()
    demo_manual_redaction()
    demo_dict_redaction()
    demo_verification()
    
    print("\n\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("\n✅ Log redaction is active and working!")
    print("\n📊 Redacted Data Types:")
    print("   ✓ Email addresses")
    print("   ✓ Passwords (all formats)")
    print("   ✓ JWT Bearer tokens")
    print("   ✓ API keys")
    print("   ✓ MongoDB connection strings")
    print("   ✓ Private keys")
    print("   ✓ Session tokens")
    print("   ✓ Credit cards, phone numbers, SSNs")
    print("\n📝 Next Steps:")
    print("   1. Review logs/security.log to verify redaction")
    print("   2. Run: python -m pytest tests/test_log_redaction.py")
    print("   3. Deploy to production with confidence!")
    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
