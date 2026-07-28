"""
Sensitive Data Filter

Automatically redacts sensitive information from log records to prevent
PII exposure and comply with security best practices (GDPR, OWASP).

Usage:
    Add to Django LOGGING configuration:
    
    LOGGING = {
        'filters': {
            'sensitive_data': {
                '()': 'src.infrastructure.logging.sensitive_filter.SensitiveDataFilter',
            }
        },
        'handlers': {
            'security_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filters': ['sensitive_data'],
                ...
            }
        }
    }

Security Categories:
    - Email addresses
    - Passwords (in various formats)
    - JWT Bearer tokens
    - API keys
    - MongoDB connection strings
    - Private keys
    - Session tokens
    - Credit card numbers (future)
"""

import re
import logging
from typing import Dict, Tuple, Optional


class SensitiveDataFilter(logging.Filter):
    """
    Logging filter that redacts sensitive data from log messages.
    
    This filter scans log messages and replaces sensitive patterns with
    redacted placeholders to prevent PII exposure in log files.
    
    Attributes:
        PATTERNS: Dictionary of regex patterns and their replacements
    """
    
    # Pattern format: (regex_pattern, replacement_string)
    # NOTE: Order matters! More specific patterns (MongoDB URIs) should come before generic ones (emails)
    PATTERNS: Dict[str, Tuple[str, str]] = {
        # MongoDB connection strings with credentials (MUST come before email pattern)
        'mongodb_uri': (
            r'mongodb(\+srv)?://[^:/@]+:[^@/]+@',
            r'mongodb\1://***REDACTED***:***REDACTED***@'
        ),
        
        # Email addresses (RFC 5322 simplified)
        'email': (
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            '***EMAIL_REDACTED***'
        ),
        
        # Passwords in various formats
        'password_colon': (
            r'password["\']?\s*:\s*["\']?([^"\'}\s,\]]+)',
            'password: "***REDACTED***"'
        ),
        'password_equals': (
            r'password["\']?\s*=\s*["\']?([^"\'}\s,\]]+)',
            'password="***REDACTED***"'
        ),
        'password_field': (
            r'(["\']password["\'])\s*:\s*["\']([^"\']+)["\']',
            r'\1: "***REDACTED***"'
        ),
        
        # JWT Bearer tokens
        'bearer_token': (
            r'Bearer\s+[A-Za-z0-9\-._~+/]+=*',
            'Bearer ***TOKEN_REDACTED***'
        ),
        
        # API keys (various formats)
        'api_key_colon': (
            r'(api[_-]?key|apikey)["\']?\s*:\s*["\']?([^"\'}\s,\]]{20,})',
            r'\1: "***REDACTED***"'
        ),
        'api_key_equals': (
            r'(api[_-]?key|apikey)["\']?\s*=\s*["\']?([^"\'}\s,\]]{20,})',
            r'\1="***REDACTED***"'
        ),
        
        # Private keys (SSH, deployment credentials, etc.)
        'private_key': (
            r'(private[_-]?key|privatekey)["\']?\s*[:=]\s*["\']?([0-9a-fA-Fx]{40,})',
            r'\1="***REDACTED***"'
        ),
        
        # Session tokens/IDs
        'session_token': (
            r'(session[_-]?token|sessiontoken|session[_-]?id)["\']?\s*[:=]\s*["\']?([^"\'}\s,\]]{20,})',
            r'\1="***REDACTED***"'
        ),
        
        # Generic secrets
        'secret_key': (
            r'(secret[_-]?key|secretkey)["\']?\s*[:=]\s*["\']?([^"\'}\s,\]]{20,})',
            r'\1="***REDACTED***"'
        ),
        
        # Credit card numbers (PAN) - basic pattern
        'credit_card': (
            r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
            '***CARD_REDACTED***'
        ),
        
        # Phone numbers (international format)
        'phone_international': (
            r'\+\d{1,3}[\s.-]?\(?\d{1,4}\)?[\s.-]?\d{1,4}[\s.-]?\d{1,9}',
            '***PHONE_REDACTED***'
        ),
        
        # Social Security Numbers (US format)
        'ssn': (
            r'\b\d{3}-\d{2}-\d{4}\b',
            '***SSN_REDACTED***'
        ),
    }
    
    def __init__(self, name: str = ''):
        """
        Initialize the sensitive data filter.
        
        Args:
            name: Filter name (optional)
        """
        super().__init__(name)
        
        # Compile patterns for better performance
        # Preserve order from PATTERNS dict (Python 3.7+ guarantees dict order)
        self._compiled_patterns = [
            (pattern_name, re.compile(pattern, re.IGNORECASE), replacement)
            for pattern_name, (pattern, replacement) in self.PATTERNS.items()
        ]
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter a log record by redacting sensitive data.
        
        Args:
            record: The log record to filter
        
        Returns:
            Always True (record is not suppressed, only modified)
        """
        # Redact message
        if isinstance(record.msg, str):
            record.msg = self._redact_sensitive_data(record.msg)
        
        # Redact args (if they're strings)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: self._redact_sensitive_data(v) if isinstance(v, str) else v
                    for k, v in record.args.items()
                }
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    self._redact_sensitive_data(arg) if isinstance(arg, str) else arg
                    for arg in record.args
                )
        
        return True
    
    def _redact_sensitive_data(self, text: str) -> str:
        """
        Apply all redaction patterns to a text string.
        
        Patterns are applied in order from PATTERNS dict, which matters because
        more specific patterns (MongoDB URIs) must be processed before generic
        ones (emails) to avoid incorrect matches.
        
        Args:
            text: The text to redact
        
        Returns:
            Text with sensitive data replaced by placeholders
        """
        redacted = text
        
        # Apply patterns in order (list preserves order)
        for pattern_name, compiled_pattern, replacement in self._compiled_patterns:
            redacted = compiled_pattern.sub(replacement, redacted)
        
        return redacted
    
    @staticmethod
    def redact_dict(data: dict, sensitive_keys: Optional[list] = None) -> dict:
        """
        Redact sensitive keys from a dictionary (for structured logging).
        
        Args:
            data: Dictionary to redact
            sensitive_keys: List of keys to redact (defaults to common sensitive keys)
        
        Returns:
            Dictionary with sensitive values redacted
        """
        if sensitive_keys is None:
            sensitive_keys = [
                'password', 'password_hash', 'secret', 'secret_key',
                'api_key', 'token', 'access_token', 'refresh_token',
                'private_key', 'session_id', 'session_token',
                'credit_card', 'card_number', 'cvv', 'ssn',
                'email', 'phone', 'phone_number'
            ]
        
        redacted = data.copy()
        
        for key in sensitive_keys:
            if key in redacted:
                redacted[key] = '***REDACTED***'
        
        # Recursive redaction for nested dicts
        for key, value in redacted.items():
            if isinstance(value, dict):
                redacted[key] = SensitiveDataFilter.redact_dict(value, sensitive_keys)
            elif isinstance(value, list):
                redacted[key] = [
                    SensitiveDataFilter.redact_dict(item, sensitive_keys)
                    if isinstance(item, dict) else item
                    for item in value
                ]
        
        return redacted


# Convenience function for manual redaction
def redact_sensitive_data(text: str) -> str:
    """
    Manually redact sensitive data from a string.
    
    Args:
        text: The text to redact
    
    Returns:
        Redacted text
    """
    filter_instance = SensitiveDataFilter()
    return filter_instance._redact_sensitive_data(text)
