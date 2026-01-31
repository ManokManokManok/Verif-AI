"""
Security Configuration Validator

Validates security-critical environment variables at startup.
This module should be imported early in the application lifecycle
to fail fast if configuration is insecure.

OWASP Reference:
- Secure Configuration: https://cheatsheetseries.owasp.org/cheatsheets/Configuration_Cheat_Sheet.html
"""

import os
import re
import logging
import sys

logger = logging.getLogger(__name__)


class SecurityConfigurationError(Exception):
    """Raised when security configuration is invalid."""
    pass


def validate_secret_key(key_name: str, value: str, min_length: int = 50) -> None:
    """
    Validate that a secret key meets security requirements.
    
    Args:
        key_name: Name of the environment variable
        value: The secret value to validate
        min_length: Minimum required length
        
    Raises:
        SecurityConfigurationError: If validation fails
    """
    if not value:
        raise SecurityConfigurationError(
            f"{key_name} is not set. "
            f"Generate with: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
        )
    
    if len(value) < min_length:
        raise SecurityConfigurationError(
            f"{key_name} is too short ({len(value)} chars). "
            f"Must be at least {min_length} characters for production security."
        )
    
    # Check for weak/default values
    weak_patterns = [
        r'^(test|dev|secret|password|key|change.?me|your.?secret)',
        r'^[a-z]{5,20}$',  # Simple lowercase words
        r'^.{1,20}$',  # Too short for meaningful entropy
    ]
    
    for pattern in weak_patterns:
        if re.match(pattern, value, re.IGNORECASE):
            logger.warning(
                f"SECURITY WARNING: {key_name} appears to be a weak or default value. "
                f"Generate a strong random key for production."
            )


def validate_debug_mode() -> None:
    """
    Validate that debug mode is disabled in production.
    
    Checks for indicators of production environment and warns/errors
    if DEBUG is enabled.
    """
    debug = os.getenv('DJANGO_DEBUG', 'False').lower() in ('1', 'true', 'yes')
    
    # Indicators that this might be production
    is_production_likely = (
        os.getenv('DJANGO_ALLOWED_HOSTS', '') and
        '*' not in os.getenv('DJANGO_ALLOWED_HOSTS', '') and
        'localhost' not in os.getenv('DJANGO_ALLOWED_HOSTS', '').lower() and
        '127.0.0.1' not in os.getenv('DJANGO_ALLOWED_HOSTS', '')
    )
    
    if debug and is_production_likely:
        raise SecurityConfigurationError(
            "DJANGO_DEBUG is enabled but DJANGO_ALLOWED_HOSTS suggests production. "
            "Set DJANGO_DEBUG=False for production deployments."
        )
    
    if debug:
        logger.warning(
            "SECURITY WARNING: Debug mode is enabled. "
            "Disable in production (DJANGO_DEBUG=False)."
        )


def validate_allowed_hosts() -> None:
    """
    Validate ALLOWED_HOSTS configuration.
    
    Ensures no wildcards are used in production.
    """
    allowed_hosts = os.getenv('DJANGO_ALLOWED_HOSTS', '')
    debug = os.getenv('DJANGO_DEBUG', 'False').lower() in ('1', 'true', 'yes')
    
    if not debug and '*' in allowed_hosts:
        raise SecurityConfigurationError(
            "DJANGO_ALLOWED_HOSTS contains wildcard (*). "
            "Specify exact hostnames in production."
        )
    
    if not debug and not allowed_hosts:
        raise SecurityConfigurationError(
            "DJANGO_ALLOWED_HOSTS is not set. "
            "Required for production deployments."
        )


def validate_cors_configuration() -> None:
    """
    Validate CORS configuration.
    
    Warns about overly permissive settings.
    """
    cors_origins = os.getenv('CORS_ALLOWED_ORIGINS', '')
    debug = os.getenv('DJANGO_DEBUG', 'False').lower() in ('1', 'true', 'yes')
    
    if not cors_origins and not debug:
        logger.warning(
            "SECURITY WARNING: CORS_ALLOWED_ORIGINS is not set. "
            "Cross-origin requests may be blocked."
        )
    
    if '*' in cors_origins:
        raise SecurityConfigurationError(
            "CORS_ALLOWED_ORIGINS contains wildcard. "
            "Specify exact origins to prevent unauthorized access."
        )


def validate_blockchain_config() -> None:
    """
    Validate blockchain configuration security.
    
    Checks that private keys are not exposed in logs or default values.
    """
    chain_enabled = os.getenv('CHAIN_ENABLED', 'false').lower() in ('true', '1', 'yes')
    private_key = os.getenv('CHAIN_PRIVATE_KEY', '')
    
    if not chain_enabled:
        return  # No validation needed if blockchain is disabled
    
    if not private_key:
        raise SecurityConfigurationError(
            "CHAIN_ENABLED is true but CHAIN_PRIVATE_KEY is not set."
        )
    
    # Check for obvious test/default keys
    if private_key.startswith('0x_your_') or private_key == '0x' + '0' * 64:
        raise SecurityConfigurationError(
            "CHAIN_PRIVATE_KEY appears to be a placeholder value. "
            "Set a real private key for blockchain operations."
        )


def validate_jwt_config() -> None:
    """
    Validate JWT configuration.
    
    Ensures secret key is strong and token lifetimes are reasonable.
    """
    jwt_secret = os.getenv('JWT_SECRET_KEY', '')
    access_lifetime = int(os.getenv('JWT_ACCESS_TOKEN_LIFETIME', '900'))
    refresh_lifetime = int(os.getenv('JWT_REFRESH_TOKEN_LIFETIME', '604800'))
    debug = os.getenv('DJANGO_DEBUG', 'False').lower() in ('1', 'true', 'yes')
    
    # Only enforce strict validation in production
    if not debug:
        validate_secret_key('JWT_SECRET_KEY', jwt_secret, min_length=64)
    elif not jwt_secret:
        raise SecurityConfigurationError("JWT_SECRET_KEY is not set")
    
    # Warn about unusual token lifetimes
    if access_lifetime > 3600:  # > 1 hour
        logger.warning(
            f"SECURITY WARNING: JWT_ACCESS_TOKEN_LIFETIME is {access_lifetime}s (>{60}min). "
            f"Consider shorter lifetimes for better security."
        )
    
    if refresh_lifetime > 2592000:  # > 30 days
        logger.warning(
            f"SECURITY WARNING: JWT_REFRESH_TOKEN_LIFETIME is very long ({refresh_lifetime}s). "
            f"Consider shorter refresh token lifetimes."
        )


def run_security_validation(strict: bool = None) -> bool:
    """
    Run all security validations.
    
    Args:
        strict: If True, raise exception on any issue. If False, only log warnings.
                If None, auto-detect based on DEBUG setting.
                
    Returns:
        True if all validations pass, False otherwise
        
    Raises:
        SecurityConfigurationError: If strict mode and validation fails
    """
    if strict is None:
        strict = os.getenv('DJANGO_DEBUG', 'False').lower() not in ('1', 'true', 'yes')
    
    validations = [
        validate_jwt_config,
        validate_debug_mode,
        validate_allowed_hosts,
        validate_cors_configuration,
        validate_blockchain_config,
    ]
    
    all_passed = True
    
    for validation in validations:
        try:
            validation()
        except SecurityConfigurationError as e:
            all_passed = False
            if strict:
                logger.error(f"Security validation failed: {e}")
                raise
            else:
                logger.warning(f"Security validation warning: {e}")
    
    if all_passed:
        logger.info("All security configuration validations passed")
    
    return all_passed


# Run validation when module is imported (optional - can be called explicitly)
if os.getenv('VALIDATE_SECURITY_CONFIG', 'false').lower() in ('1', 'true', 'yes'):
    try:
        run_security_validation()
    except SecurityConfigurationError as e:
        logger.critical(f"FATAL: Security configuration error: {e}")
        sys.exit(1)
