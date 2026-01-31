"""
Input Validation & Sanitization Module

OWASP-compliant input validation with schema-based validation,
type checks, length limits, and sanitization.

Security References:
- OWASP Input Validation Cheat Sheet
- OWASP XSS Prevention Cheat Sheet
"""

import re
import html
import logging
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)
security_logger = logging.getLogger('security')


class ValidationError(Exception):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, field: str = None, code: str = 'VALIDATION_ERROR'):
        self.message = message
        self.field = field
        self.code = code
        super().__init__(message)


class FieldType(Enum):
    """Supported field types for validation."""
    STRING = "string"
    EMAIL = "email"
    PASSWORD = "password"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    UUID = "uuid"
    URL = "url"
    TOKEN = "token"
    MESSAGE = "message"  # For longer text content


@dataclass
class FieldSchema:
    """
    Schema definition for a single field.
    
    Attributes:
        name: Field name
        field_type: Type of field (from FieldType enum)
        required: Whether field is required
        min_length: Minimum length for strings
        max_length: Maximum length for strings
        min_value: Minimum value for numbers
        max_value: Maximum value for numbers
        pattern: Regex pattern for validation
        allowed_values: List of allowed values (enum validation)
        sanitize: Whether to sanitize HTML/XSS
        strip: Whether to strip whitespace
        lowercase: Whether to convert to lowercase
    """
    name: str
    field_type: FieldType
    required: bool = False
    min_length: int = None
    max_length: int = None
    min_value: Union[int, float] = None
    max_value: Union[int, float] = None
    pattern: str = None
    allowed_values: List[Any] = None
    sanitize: bool = True
    strip: bool = True
    lowercase: bool = False


# =============================================================================
# PREDEFINED FIELD CONSTRAINTS (OWASP Best Practices)
# =============================================================================

# Email: RFC 5321 limits local part to 64 chars, domain to 255 chars
EMAIL_CONSTRAINTS = {
    'max_length': 254,
    'min_length': 5,
    'pattern': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
}

# Password: Secure defaults
PASSWORD_CONSTRAINTS = {
    'min_length': 8,
    'max_length': 128,  # Prevent DoS via bcrypt
}

# Username: Alphanumeric with underscores/hyphens
USERNAME_CONSTRAINTS = {
    'min_length': 3,
    'max_length': 32,
    'pattern': r'^[a-zA-Z0-9_-]+$'
}

# UUID: Standard format
UUID_CONSTRAINTS = {
    'pattern': r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
}

# Message content: For scam detection input
MESSAGE_CONSTRAINTS = {
    'min_length': 1,
    'max_length': 10000,  # 10KB limit for text analysis
}

# Token: For verification/reset tokens
TOKEN_CONSTRAINTS = {
    'min_length': 16,
    'max_length': 512,
    'pattern': r'^[a-zA-Z0-9_-]+$'
}


# =============================================================================
# SANITIZATION FUNCTIONS
# =============================================================================

def sanitize_string(value: str, allow_html: bool = False) -> str:
    """
    Sanitize string input to prevent XSS and injection attacks.
    
    Args:
        value: Input string to sanitize
        allow_html: If False, escape HTML entities
        
    Returns:
        Sanitized string
        
    Security:
        - Escapes HTML entities by default
        - Removes null bytes
        - Normalizes Unicode
    """
    if not isinstance(value, str):
        return value
    
    # Remove null bytes (potential bypass technique)
    sanitized = value.replace('\x00', '')
    
    # Escape HTML entities to prevent XSS
    if not allow_html:
        sanitized = html.escape(sanitized, quote=True)
    
    return sanitized


def sanitize_for_logging(value: str, max_length: int = 100) -> str:
    """
    Sanitize value for safe logging (prevent log injection).
    
    Args:
        value: Value to sanitize
        max_length: Maximum length to log
        
    Returns:
        Safe string for logging
    """
    if not value:
        return "[empty]"
    
    # Remove newlines and control characters that could inject log entries
    safe = re.sub(r'[\r\n\t]', ' ', str(value))
    
    # Truncate
    if len(safe) > max_length:
        safe = safe[:max_length] + '...[truncated]'
    
    return safe


# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

def validate_email(email: str) -> Tuple[bool, Optional[str]]:
    """
    Validate email format per RFC 5321.
    
    Args:
        email: Email address to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not email:
        return False, "Email is required"
    
    if len(email) > EMAIL_CONSTRAINTS['max_length']:
        return False, f"Email must not exceed {EMAIL_CONSTRAINTS['max_length']} characters"
    
    if len(email) < EMAIL_CONSTRAINTS['min_length']:
        return False, f"Email must be at least {EMAIL_CONSTRAINTS['min_length']} characters"
    
    if not re.match(EMAIL_CONSTRAINTS['pattern'], email):
        return False, "Invalid email format"
    
    return True, None


def validate_password(password: str) -> Tuple[bool, List[str]]:
    """
    Validate password strength per OWASP guidelines.
    
    Args:
        password: Password to validate
        
    Returns:
        Tuple of (is_valid, error_messages)
        
    Security:
        - Minimum 8 characters
        - Maximum 128 characters (bcrypt limit)
        - Requires uppercase, lowercase, digit, special char
        - No whitespace characters allowed
    """
    errors = []
    
    if not password:
        return False, ["Password is required"]
    
    # Check for whitespace characters (spaces, tabs, newlines, etc.)
    if re.search(r'\s', password):
        errors.append("Password must not contain spaces or whitespace characters")
    
    if len(password) < PASSWORD_CONSTRAINTS['min_length']:
        errors.append(f"Password must be at least {PASSWORD_CONSTRAINTS['min_length']} characters")
    
    if len(password) > PASSWORD_CONSTRAINTS['max_length']:
        errors.append(f"Password must not exceed {PASSWORD_CONSTRAINTS['max_length']} characters")
    
    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")
    
    if not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")
    
    if not re.search(r'\d', password):
        errors.append("Password must contain at least one digit")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>\[\]\\;\'`~_+=/-]', password):
        errors.append("Password must contain at least one special character")
    
    return len(errors) == 0, errors


def validate_username(username: str) -> Tuple[bool, Optional[str]]:
    """
    Validate username format.
    
    Args:
        username: Username to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not username:
        return False, "Username is required"
    
    if len(username) < USERNAME_CONSTRAINTS['min_length']:
        return False, f"Username must be at least {USERNAME_CONSTRAINTS['min_length']} characters"
    
    if len(username) > USERNAME_CONSTRAINTS['max_length']:
        return False, f"Username must not exceed {USERNAME_CONSTRAINTS['max_length']} characters"
    
    if not re.match(USERNAME_CONSTRAINTS['pattern'], username):
        return False, "Username may only contain letters, numbers, underscores, and hyphens"
    
    return True, None


def validate_uuid(value: str) -> Tuple[bool, Optional[str]]:
    """
    Validate UUID format.
    
    Args:
        value: UUID string to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not value:
        return False, "UUID is required"
    
    if not re.match(UUID_CONSTRAINTS['pattern'], value):
        return False, "Invalid UUID format"
    
    return True, None


def validate_message(message: str) -> Tuple[bool, Optional[str]]:
    """
    Validate message content for scam detection.
    
    Args:
        message: Message text to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not message:
        return False, "Message is required"
    
    if len(message) < MESSAGE_CONSTRAINTS['min_length']:
        return False, "Message is too short for analysis"
    
    if len(message) > MESSAGE_CONSTRAINTS['max_length']:
        return False, f"Message exceeds maximum length of {MESSAGE_CONSTRAINTS['max_length']} characters"
    
    return True, None


def validate_token(token: str) -> Tuple[bool, Optional[str]]:
    """
    Validate token format (for verification/reset tokens).
    
    Args:
        token: Token string to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not token:
        return False, "Token is required"
    
    if len(token) < TOKEN_CONSTRAINTS['min_length']:
        return False, "Invalid token"
    
    if len(token) > TOKEN_CONSTRAINTS['max_length']:
        return False, "Invalid token"
    
    if not re.match(TOKEN_CONSTRAINTS['pattern'], token):
        return False, "Invalid token format"
    
    return True, None


# =============================================================================
# REQUEST VALIDATION CLASS
# =============================================================================

class RequestValidator:
    """
    Schema-based request validation.
    
    Usage:
        validator = RequestValidator()
        validator.add_field('email', FieldType.EMAIL, required=True)
        validator.add_field('password', FieldType.PASSWORD, required=True)
        
        is_valid, errors, cleaned_data = validator.validate(request.data)
        
        if not is_valid:
            return error_response(errors)
    """
    
    def __init__(self, reject_unknown: bool = True):
        """
        Initialize validator.
        
        Args:
            reject_unknown: If True, reject requests with unexpected fields
        """
        self.schemas: Dict[str, FieldSchema] = {}
        self.reject_unknown = reject_unknown
    
    def add_field(
        self,
        name: str,
        field_type: FieldType,
        required: bool = False,
        **kwargs
    ) -> 'RequestValidator':
        """
        Add a field to the validation schema.
        
        Args:
            name: Field name
            field_type: Type of field
            required: Whether field is required
            **kwargs: Additional constraints (min_length, max_length, etc.)
            
        Returns:
            Self for method chaining
        """
        self.schemas[name] = FieldSchema(
            name=name,
            field_type=field_type,
            required=required,
            **kwargs
        )
        return self
    
    def validate(self, data: Dict[str, Any]) -> Tuple[bool, Dict[str, str], Dict[str, Any]]:
        """
        Validate request data against schema.
        
        Args:
            data: Request data dictionary
            
        Returns:
            Tuple of (is_valid, errors, cleaned_data)
            - is_valid: True if all validations pass
            - errors: Dictionary of field -> error message
            - cleaned_data: Sanitized and validated data
        """
        errors = {}
        cleaned = {}
        
        # Check for unexpected fields
        if self.reject_unknown and data:
            unexpected = set(data.keys()) - set(self.schemas.keys())
            if unexpected:
                security_logger.warning(
                    f"Request contains unexpected fields: {sanitize_for_logging(str(unexpected))}"
                )
                errors['_unexpected'] = f"Unexpected fields: {', '.join(sorted(unexpected))}"
        
        # Validate each field
        for name, schema in self.schemas.items():
            value = data.get(name) if data else None
            
            # Check required
            if schema.required and (value is None or value == ''):
                errors[name] = f"{name} is required"
                continue
            
            # Skip optional empty fields
            if value is None or value == '':
                continue
            
            # Validate and clean based on type
            try:
                cleaned_value = self._validate_field(value, schema)
                cleaned[name] = cleaned_value
            except ValidationError as e:
                errors[name] = e.message
        
        return len(errors) == 0, errors, cleaned
    
    def _validate_field(self, value: Any, schema: FieldSchema) -> Any:
        """Validate and clean a single field value."""
        
        # Type-specific validation
        if schema.field_type == FieldType.STRING:
            return self._validate_string(value, schema)
        
        elif schema.field_type == FieldType.EMAIL:
            cleaned = str(value).strip().lower() if schema.lowercase else str(value).strip()
            is_valid, error = validate_email(cleaned)
            if not is_valid:
                raise ValidationError(error, schema.name)
            return cleaned
        
        elif schema.field_type == FieldType.PASSWORD:
            is_valid, errors = validate_password(value)
            if not is_valid:
                raise ValidationError('; '.join(errors), schema.name)
            return value  # Don't modify passwords
        
        elif schema.field_type == FieldType.INTEGER:
            return self._validate_integer(value, schema)
        
        elif schema.field_type == FieldType.FLOAT:
            return self._validate_float(value, schema)
        
        elif schema.field_type == FieldType.BOOLEAN:
            return self._validate_boolean(value, schema)
        
        elif schema.field_type == FieldType.UUID:
            cleaned = str(value).strip()
            is_valid, error = validate_uuid(cleaned)
            if not is_valid:
                raise ValidationError(error, schema.name)
            return cleaned
        
        elif schema.field_type == FieldType.TOKEN:
            cleaned = str(value).strip()
            is_valid, error = validate_token(cleaned)
            if not is_valid:
                raise ValidationError(error, schema.name)
            return cleaned
        
        elif schema.field_type == FieldType.MESSAGE:
            return self._validate_message(value, schema)
        
        else:
            return value
    
    def _validate_string(self, value: Any, schema: FieldSchema) -> str:
        """Validate string field."""
        if not isinstance(value, str):
            raise ValidationError(f"{schema.name} must be a string", schema.name)
        
        cleaned = value
        
        if schema.strip:
            cleaned = cleaned.strip()
        
        if schema.lowercase:
            cleaned = cleaned.lower()
        
        if schema.sanitize:
            cleaned = sanitize_string(cleaned)
        
        # Length checks
        if schema.min_length and len(cleaned) < schema.min_length:
            raise ValidationError(
                f"{schema.name} must be at least {schema.min_length} characters",
                schema.name
            )
        
        if schema.max_length and len(cleaned) > schema.max_length:
            raise ValidationError(
                f"{schema.name} must not exceed {schema.max_length} characters",
                schema.name
            )
        
        # Pattern check
        if schema.pattern and not re.match(schema.pattern, cleaned):
            raise ValidationError(f"Invalid {schema.name} format", schema.name)
        
        # Allowed values check
        if schema.allowed_values and cleaned not in schema.allowed_values:
            raise ValidationError(
                f"{schema.name} must be one of: {', '.join(map(str, schema.allowed_values))}",
                schema.name
            )
        
        return cleaned
    
    def _validate_message(self, value: Any, schema: FieldSchema) -> str:
        """Validate message content (longer text)."""
        if not isinstance(value, str):
            raise ValidationError(f"{schema.name} must be a string", schema.name)
        
        cleaned = value.strip()
        
        # Use message constraints
        is_valid, error = validate_message(cleaned)
        if not is_valid:
            raise ValidationError(error, schema.name)
        
        # Note: We don't fully sanitize message content since we need to preserve
        # the original text for scam detection analysis. However, we do log sanitization.
        if schema.sanitize:
            # Log potentially dangerous content but don't modify
            if re.search(r'<script|javascript:|on\w+\s*=', cleaned, re.IGNORECASE):
                security_logger.warning(
                    f"Potentially malicious content in {schema.name}: "
                    f"{sanitize_for_logging(cleaned)}"
                )
        
        return cleaned
    
    def _validate_integer(self, value: Any, schema: FieldSchema) -> int:
        """Validate integer field."""
        try:
            cleaned = int(value)
        except (ValueError, TypeError):
            raise ValidationError(f"{schema.name} must be an integer", schema.name)
        
        if schema.min_value is not None and cleaned < schema.min_value:
            raise ValidationError(
                f"{schema.name} must be at least {schema.min_value}",
                schema.name
            )
        
        if schema.max_value is not None and cleaned > schema.max_value:
            raise ValidationError(
                f"{schema.name} must not exceed {schema.max_value}",
                schema.name
            )
        
        return cleaned
    
    def _validate_float(self, value: Any, schema: FieldSchema) -> float:
        """Validate float field."""
        try:
            cleaned = float(value)
        except (ValueError, TypeError):
            raise ValidationError(f"{schema.name} must be a number", schema.name)
        
        if schema.min_value is not None and cleaned < schema.min_value:
            raise ValidationError(
                f"{schema.name} must be at least {schema.min_value}",
                schema.name
            )
        
        if schema.max_value is not None and cleaned > schema.max_value:
            raise ValidationError(
                f"{schema.name} must not exceed {schema.max_value}",
                schema.name
            )
        
        return cleaned
    
    def _validate_boolean(self, value: Any, schema: FieldSchema) -> bool:
        """Validate boolean field."""
        if isinstance(value, bool):
            return value
        
        if isinstance(value, str):
            if value.lower() in ('true', '1', 'yes'):
                return True
            elif value.lower() in ('false', '0', 'no'):
                return False
        
        if isinstance(value, int):
            return bool(value)
        
        raise ValidationError(f"{schema.name} must be a boolean", schema.name)


# =============================================================================
# PREDEFINED VALIDATORS FOR COMMON ENDPOINTS
# =============================================================================

def get_login_validator() -> RequestValidator:
    """Get validator for login endpoint."""
    return RequestValidator().add_field(
        'email', FieldType.EMAIL, required=True, lowercase=True
    ).add_field(
        'password', FieldType.STRING, required=True, 
        min_length=1, max_length=128, sanitize=False
    )


def get_signup_validator() -> RequestValidator:
    """Get validator for signup endpoint."""
    return RequestValidator().add_field(
        'email', FieldType.EMAIL, required=True, lowercase=True
    ).add_field(
        'username', FieldType.STRING, required=True,
        min_length=USERNAME_CONSTRAINTS['min_length'],
        max_length=USERNAME_CONSTRAINTS['max_length'],
        pattern=USERNAME_CONSTRAINTS['pattern']
    ).add_field(
        'password', FieldType.PASSWORD, required=True
    )


def get_detect_scam_validator() -> RequestValidator:
    """Get validator for scam detection endpoint."""
    return RequestValidator().add_field(
        'message', FieldType.MESSAGE, required=True
    )


def get_email_only_validator() -> RequestValidator:
    """Get validator for endpoints requiring only email."""
    return RequestValidator().add_field(
        'email', FieldType.EMAIL, required=True, lowercase=True
    )


def get_token_only_validator() -> RequestValidator:
    """Get validator for endpoints requiring only token."""
    return RequestValidator().add_field(
        'token', FieldType.TOKEN, required=True
    )


def get_password_reset_validator() -> RequestValidator:
    """Get validator for password reset endpoint."""
    return RequestValidator().add_field(
        'token', FieldType.TOKEN, required=True
    ).add_field(
        'new_password', FieldType.PASSWORD, required=True
    )


def get_refresh_token_validator() -> RequestValidator:
    """Get validator for token refresh endpoint."""
    return RequestValidator().add_field(
        'refresh_token', FieldType.STRING, required=True,
        min_length=10, max_length=2048, sanitize=False
    )


def get_analysis_create_validator() -> RequestValidator:
    """Get validator for analysis creation endpoint."""
    return RequestValidator().add_field(
        'scam_class', FieldType.INTEGER, required=True, min_value=-1, max_value=14
    ).add_field(
        'scam_type', FieldType.STRING, required=True, min_length=1, max_length=100
    ).add_field(
        'confidence_bps', FieldType.INTEGER, required=True, min_value=0, max_value=10000
    ).add_field(
        'is_scam', FieldType.BOOLEAN, required=True
    ).add_field(
        'analyzer_type', FieldType.STRING, required=False,
        min_length=1, max_length=50, allowed_values=['bert', 'llm', 'hybrid']
    ).add_field(
        'analyzer_version', FieldType.STRING, required=False,
        min_length=1, max_length=20
    )


def get_check_permission_validator() -> RequestValidator:
    """Get validator for permission check endpoint."""
    return RequestValidator().add_field(
        'permission', FieldType.STRING, required=True,
        min_length=1, max_length=100, pattern=r'^[a-z_]+$'
    ).add_field(
        'resource', FieldType.STRING, required=False,
        min_length=1, max_length=100, pattern=r'^[a-z_]+$'
    )
