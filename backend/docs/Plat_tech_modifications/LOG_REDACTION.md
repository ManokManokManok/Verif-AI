# Log Redaction Implementation

## Overview

The log redaction system automatically removes sensitive data (emails, passwords, tokens, etc.) from all log outputs to prevent PII exposure and ensure GDPR compliance.

## Components

### 1. SensitiveDataFilter
**Location:** `backend/src/infrastructure/logging/sensitive_filter.py`

A logging filter that scans log messages and redacts sensitive patterns before they're written to log files.

**Redacted Data Types:**
- ✅ Email addresses
- ✅ Passwords (all formats: `password:`, `password=`, JSON)
- ✅ JWT Bearer tokens
- ✅ API keys
- ✅ MongoDB connection strings with credentials
- ✅ Private keys (SSH, deployment credentials)
- ✅ Session tokens
- ✅ Credit card numbers
- ✅ Phone numbers (international format)
- ✅ Social Security Numbers

### 2. Django Integration
**Location:** `backend/verfai/settings.py`

The filter is automatically applied to all log handlers in Django's logging configuration:

```python
LOGGING = {
    'filters': {
        'sensitive_data': {
            '()': 'src.infrastructure.logging.sensitive_filter.SensitiveDataFilter',
        }
    },
    'handlers': {
        'console': {
            'filters': ['sensitive_data'],
            ...
        },
        'security_file': {
            'filters': ['sensitive_data'],
            ...
        }
    }
}
```

### 3. Unit Tests
**Location:** `backend/tests/test_log_redaction.py`

Comprehensive test suite with 25+ test cases covering:
- Email redaction
- Password redaction (multiple formats)
- Token redaction (Bearer, API keys)
- MongoDB URI redaction
- Private key redaction
- Credit card, phone, SSN redaction
- Dictionary redaction (structured logging)
- Manual redaction function

## Usage

### Automatic Redaction (Django Logging)

All logging through Django's logging system is automatically redacted:

```python
import logging

logger = logging.getLogger('security')

# This will be redacted automatically
logger.info("User admin@example.com logged in with password=secret123")
# Output: "User ***EMAIL_REDACTED*** logged in with password=***REDACTED***"

# Bearer tokens are redacted
logger.info(f"Authorization: Bearer {access_token}")
# Output: "Authorization: Bearer ***TOKEN_REDACTED***"

# MongoDB URIs are redacted
logger.info(f"Connecting to {mongodb_uri}")
# Output: "Connecting to mongodb+srv://***REDACTED***:***REDACTED***@cluster.mongodb.net/"
```

### Manual Redaction

For cases where you need to manually redact a string:

```python
from src.infrastructure.logging.sensitive_filter import redact_sensitive_data

# Redact a string manually
text = "Contact support@verif-ai.com for API key: sk_live_abc123"
safe_text = redact_sensitive_data(text)
print(safe_text)
# Output: "Contact ***EMAIL_REDACTED*** for API key: ***REDACTED***"
```

### Dictionary Redaction (Structured Logging)

For redacting sensitive keys in dictionaries before logging:

```python
from src.infrastructure.logging.sensitive_filter import SensitiveDataFilter

# Redact sensitive dictionary keys
user_data = {
    "username": "admin",
    "password": "secret123",
    "email": "admin@example.com",
    "role": "administrator"
}

safe_data = SensitiveDataFilter.redact_dict(user_data)
logger.info(f"User data: {safe_data}")
# Output: {"username": "admin", "password": "***REDACTED***", "email": "***REDACTED***", "role": "administrator"}

# Custom sensitive keys
data = {"api_token": "xyz", "internal_id": "123"}
safe = SensitiveDataFilter.redact_dict(data, sensitive_keys=["api_token"])
```

### MongoDB Repository Usage

When logging MongoDB queries, use redaction for safety:

```python
from src.infrastructure.logging.sensitive_filter import SensitiveDataFilter

def update_user_password(user_id, new_password):
    query = {"_id": user_id}
    update = {"$set": {"password_hash": hash_password(new_password)}}
    
    # Redact before logging
    safe_update = SensitiveDataFilter.redact_dict(update)
    logger.debug(f"MongoDB update: {safe_update}")
    
    collection.update_one(query, update)
```

## Testing

Run the log redaction tests:

```powershell
# Run all redaction tests
python -m pytest tests/test_log_redaction.py -v

# Run specific test
python -m pytest tests/test_log_redaction.py::TestSensitiveDataFilter::test_email_redacted -v

# Run with coverage
python -m pytest tests/test_log_redaction.py --cov=src.infrastructure.logging
```

Expected output:
```
tests/test_log_redaction.py::TestSensitiveDataFilter::test_email_redacted PASSED
tests/test_log_redaction.py::TestSensitiveDataFilter::test_password_colon_format_redacted PASSED
tests/test_log_redaction.py::TestSensitiveDataFilter::test_bearer_token_redacted PASSED
...
========================= 25 passed in 0.5s =========================
```

## Verification

### Check Log Files

After implementation, verify that sensitive data is not present in logs:

```powershell
# Search security.log for emails (should find none)
Select-String -Path backend/logs/security.log -Pattern "@" | Select-Object -First 10

# Should only find redacted placeholders
Select-String -Path backend/logs/security.log -Pattern "***EMAIL_REDACTED***"

# Check for passwords (should find none)
Select-String -Path backend/logs/security.log -Pattern "password.*:" | Where-Object { $_ -notmatch "REDACTED" }
```

### Manual Testing

Test in Django shell:

```powershell
cd backend
python manage.py shell
```

```python
import logging
logger = logging.getLogger('security')

# Test email redaction
logger.info("User test@example.com authenticated")

# Test password redaction
logger.info('Login attempt: {"username": "admin", "password": "secret"}')

# Test token redaction
logger.info("Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")

# Check logs/security.log - sensitive data should be redacted
```

## Performance Impact

The filter uses compiled regex patterns for efficient matching:

- **Overhead:** ~0.1-0.5ms per log message
- **Impact:** Negligible for typical logging volumes
- **Optimization:** Patterns are compiled once at initialization

## Security Notes

### What is Redacted
✅ **Log files** (console and file handlers) - All sensitive patterns removed  
✅ **Audit logs** - Automatic redaction via logging filter  
✅ **Error messages** - Stack traces with sensitive data redacted  

### What is NOT Redacted
⚠️ **MongoDB audit_logs collection** - Stores original data (access-controlled)  
⚠️ **Application memory** - Sensitive data in variables (normal operation)  
⚠️ **Database queries** - Use `redact_dict()` before logging queries  

### Best Practices

1. **Use `redact_dict()` for structured data:**
   ```python
   logger.info(f"Query: {SensitiveDataFilter.redact_dict(query)}")
   ```

2. **Never bypass the filter:**
   ```python
   # ❌ DON'T: Direct file write
   with open('log.txt', 'w') as f:
       f.write(f"Password: {password}")  # NOT REDACTED!
   
   # ✅ DO: Use logger
   logger.info(f"Password reset for user")  # Redacted automatically
   ```

3. **Add custom patterns if needed:**
   Edit `SensitiveDataFilter.PATTERNS` in `sensitive_filter.py`

4. **Test new sensitive data types:**
   Add test cases to `test_log_redaction.py`

## Compliance

This implementation helps meet the following compliance requirements:

- **GDPR Article 32:** Technical measures for data security
- **OWASP Logging Cheat Sheet:** Sensitive data exclusion
- **PCI DSS 3.2.1:** No storage of sensitive authentication data
- **HIPAA Security Rule:** Protection of ePHI in logs

## Troubleshooting

### Issue: Sensitive data still appearing in logs

**Solution:**
1. Verify filter is installed in `settings.py`
2. Check that handler has filter applied
3. Ensure logger is using configured handler
4. Test with `test_log_redaction.py`

### Issue: Too much data being redacted

**Solution:**
1. Review regex patterns in `sensitive_filter.py`
2. Make patterns more specific
3. Add test cases to prevent false positives

### Issue: Performance degradation

**Solution:**
1. Profile log statements with `cProfile`
2. Reduce logging verbosity in production
3. Consider async logging for high-volume apps

## Migration Guide

If upgrading from an older version without log redaction:

1. **Update settings.py:** Add filter configuration (already done)
2. **Review existing logs:** Check for exposed sensitive data
3. **Rotate logs:** Consider archiving/deleting old unredacted logs
4. **Update documentation:** Notify team of new redaction behavior
5. **Run tests:** Verify `pytest tests/test_log_redaction.py` passes

## Support

For issues or questions about log redaction:

- **Documentation:** This file
- **Tests:** `backend/tests/test_log_redaction.py`
- **Source:** `backend/src/infrastructure/logging/sensitive_filter.py`
- **Config:** `backend/verfai/settings.py` (LOGGING section)

---

**Status:** ✅ Implemented (February 25, 2026)  
**Last Updated:** February 25, 2026  
**Version:** 1.0
