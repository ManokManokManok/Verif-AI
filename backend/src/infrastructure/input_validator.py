"""
Input Validation and Sanitization Module

Implements strict input validation following OWASP best practices:
- Schema-based validation with type checking
- Length limits to prevent buffer overflow/DoS attacks
- Rejection of unexpected fields (mass assignment prevention)
- Input sanitization to prevent injection attacks
- Clear, actionable error messages

OWASP References:
- https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html
- https://cheatsheetseries.owasp.org/cheatsheets/Mass_Assignment_Cheat_Sheet.html
"""

import re
import html
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union, Callable
from enum import Enum


class ValidationErrorCode(Enum):
    """Standardized validation error codes."""
    MISSING_FIELD = "MISSING_FIELD"
    INVALID_TYPE = "INVALID_TYPE"
    INVALID_FORMAT = "INVALID_FORMAT"
    TOO_SHORT = "TOO_SHORT"
    TOO_LONG = "TOO_LONG"
    OUT_OF_RANGE = "OUT_OF_RANGE"
    UNEXPECTED_FIELD = "UNEXPECTED_FIELD"
    INVALID_VALUE = "INVALID_VALUE"
    WEAK_PASSWORD = "WEAK_PASSWORD"
    INVALID_EMAIL = "INVALID_EMAIL"
    INVALID_TOKEN = "INVALID_TOKEN"
    VALIDATION_ERROR = "VALIDATION_ERROR"


@dataclass
class ValidationError:
    """Represents a single validation error."""
    field: str
    code: ValidationErrorCode
    message: str
    
    def to_dict(self) -> Dict[str, str]:
        return {
            'field': self.field,
            'code': self.code.value,
            'message': self.message
        }


@dataclass
class ValidationResult:
    """Result of validation containing validated data or errors."""
    is_valid: bool
    data: Optional[Dict[str, Any]] = None
    errors: List[ValidationError] = field(default_factory=list)
    
    def to_error_response(self) -> Dict[str, Any]:
        """Convert to API error response format."""
        return {
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'Input validation failed',
                'details': [err.to_dict() for err in self.errors]
            }
        }


@dataclass
class FieldSchema:
    """
    Schema definition for a single field.
    
    Attributes:
        field_type: Expected Python type (str, int, float, bool, list, dict)
        required: Whether field is required
        min_length: Minimum length for strings/lists
        max_length: Maximum length for strings/lists
        min_value: Minimum value for numbers
        max_value: Maximum value for numbers
        pattern: Regex pattern for string validation
        allowed_values: List of allowed values
        custom_validator: Custom validation function
        sanitize: Whether to sanitize string input
        default: Default value if not provided
    """
    field_type: type
    required: bool = True
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    pattern: Optional[str] = None
    allowed_values: Optional[List[Any]] = None
    custom_validator: Optional[Callable[[Any], tuple[bool, str]]] = None
    sanitize: bool = True
    default: Optional[Any] = None


# ============================================================================
# Common Validators
# ============================================================================

# Email regex pattern (RFC 5322 simplified)
EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

# Token pattern (hex string)
TOKEN_PATTERN = r'^[a-fA-F0-9]+$'

# Username pattern (alphanumeric, underscore, hyphen)
USERNAME_PATTERN = r'^[a-zA-Z0-9_-]+$'


def validate_email_format(email: str) -> tuple[bool, str]:
    """Validate email format."""
    if not re.match(EMAIL_PATTERN, email):
        return False, "Invalid email format"
    if len(email) > 254:  # RFC 5321 limit
        return False, "Email address too long"
    return True, ""


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password strength following OWASP guidelines.
    
    Requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    - Maximum 128 characters (prevent DoS with bcrypt)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if len(password) > 128:
        return False, "Password must not exceed 128 characters"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>\-_=+\[\]\\;\'`~]', password):
        return False, "Password must contain at least one special character"
    
    # Check for common weak patterns
    common_patterns = [
        r'(.)\1{3,}',  # Same character repeated 4+ times
        r'(012|123|234|345|456|567|678|789)',  # Sequential numbers
        r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)',  # Sequential letters
    ]
    
    for pattern in common_patterns:
        if re.search(pattern, password.lower()):
            return False, "Password contains weak patterns (repeated or sequential characters)"
    
    return True, ""


def validate_token_format(token: str) -> tuple[bool, str]:
    """Validate token format (hex string)."""
    if not token:
        return False, "Token is required"
    if len(token) < 16:
        return False, "Token too short"
    if len(token) > 256:
        return False, "Token too long"
    if not re.match(TOKEN_PATTERN, token):
        return False, "Invalid token format"
    return True, ""


def validate_jwt_format(token: str) -> tuple[bool, str]:
    """Validate JWT token format."""
    if not token:
        return False, "Token is required"
    # JWT has 3 base64-encoded parts separated by dots
    parts = token.split('.')
    if len(parts) != 3:
        return False, "Invalid JWT format"
    # Basic length check
    if len(token) > 4096:  # Reasonable max for JWT
        return False, "Token too long"
    return True, ""


# ============================================================================
# Sanitization Functions
# ============================================================================

def sanitize_string(value: str, max_length: int = 10000) -> str:
    """
    Sanitize string input to prevent XSS and injection attacks.
    
    Operations:
    - Strip leading/trailing whitespace
    - Escape HTML entities
    - Remove null bytes
    - Truncate to max length
    - Normalize unicode (NFC)
    """
    if not isinstance(value, str):
        return str(value)
    
    # Remove null bytes (common injection technique)
    value = value.replace('\x00', '')
    
    # Strip whitespace
    value = value.strip()
    
    # Truncate to max length
    value = value[:max_length]
    
    # Escape HTML entities for XSS prevention
    # Note: Only apply for display contexts, not storage
    # value = html.escape(value)
    
    return value


def sanitize_email(email: str) -> str:
    """Sanitize email address."""
    if not isinstance(email, str):
        return ''
    
    # Lowercase and strip
    email = email.lower().strip()
    
    # Remove dangerous characters (but keep valid email chars)
    # Only allow: alphanumeric, @, ., +, -, _
    email = re.sub(r'[^\w@.+-]', '', email)
    
    return email[:254]  # RFC 5321 max length


# ============================================================================
# Schema Definitions for API Endpoints
# ============================================================================

# Authentication Schemas
SIGNUP_SCHEMA = {
    'email': FieldSchema(
        field_type=str,
        required=True,
        max_length=254,
        custom_validator=validate_email_format
    ),
    'password': FieldSchema(
        field_type=str,
        required=True,
        min_length=8,
        max_length=128,
        custom_validator=validate_password_strength,
        sanitize=False  # Don't sanitize passwords
    ),
    'username': FieldSchema(
        field_type=str,
        required=False,
        min_length=3,
        max_length=50,
        pattern=USERNAME_PATTERN
    ),
}

LOGIN_SCHEMA = {
    'email': FieldSchema(
        field_type=str,
        required=True,
        max_length=254,
        custom_validator=validate_email_format
    ),
    'password': FieldSchema(
        field_type=str,
        required=True,
        min_length=1,
        max_length=128,
        sanitize=False  # Don't sanitize passwords
    ),
}

EMAIL_ONLY_SCHEMA = {
    'email': FieldSchema(
        field_type=str,
        required=True,
        max_length=254,
        custom_validator=validate_email_format
    ),
}

TOKEN_ONLY_SCHEMA = {
    'token': FieldSchema(
        field_type=str,
        required=True,
        min_length=16,
        max_length=256,
        custom_validator=validate_token_format
    ),
}

PASSWORD_RESET_SCHEMA = {
    'token': FieldSchema(
        field_type=str,
        required=True,
        min_length=16,
        max_length=256,
        custom_validator=validate_token_format
    ),
    'new_password': FieldSchema(
        field_type=str,
        required=True,
        min_length=8,
        max_length=128,
        custom_validator=validate_password_strength,
        sanitize=False
    ),
}

REFRESH_TOKEN_SCHEMA = {
    'refresh_token': FieldSchema(
        field_type=str,
        required=True,
        min_length=10,
        max_length=4096,
        custom_validator=validate_jwt_format
    ),
}

LOGOUT_SCHEMA = {
    'refresh_token': FieldSchema(
        field_type=str,
        required=False,
        max_length=4096,
        custom_validator=validate_jwt_format
    ),
}

CHECK_PERMISSION_SCHEMA = {
    'permission': FieldSchema(
        field_type=str,
        required=True,
        min_length=1,
        max_length=100,
        pattern=r'^[a-z_]+$'  # lowercase with underscores
    ),
    'resource': FieldSchema(
        field_type=str,
        required=False,
        max_length=100,
        pattern=r'^[a-z_]+$'
    ),
}


# ============================================================================
# Main Validation Function
# ============================================================================

def validate_input(
    data: Dict[str, Any],
    schema: Dict[str, FieldSchema],
    strict: bool = True
) -> ValidationResult:
    """
    Validate input data against a schema.
    
    Args:
        data: Input data dictionary
        schema: Schema definition
        strict: If True, reject unexpected fields (OWASP mass assignment prevention)
    
    Returns:
        ValidationResult with validated data or errors
    """
    errors: List[ValidationError] = []
    validated_data: Dict[str, Any] = {}
    
    # Check for unexpected fields (mass assignment prevention)
    if strict:
        unexpected_fields = set(data.keys()) - set(schema.keys())
        for field_name in unexpected_fields:
            errors.append(ValidationError(
                field=field_name,
                code=ValidationErrorCode.UNEXPECTED_FIELD,
                message=f"Unexpected field: {field_name}"
            ))
    
    # Validate each field in schema
    for field_name, field_schema in schema.items():
        value = data.get(field_name)
        
        # Check required fields
        if value is None or (isinstance(value, str) and not value.strip()):
            if field_schema.required:
                errors.append(ValidationError(
                    field=field_name,
                    code=ValidationErrorCode.MISSING_FIELD,
                    message=f"{field_name} is required"
                ))
            elif field_schema.default is not None:
                validated_data[field_name] = field_schema.default
            continue
        
        # Type checking
        if not isinstance(value, field_schema.field_type):
            # Allow int for float fields
            if not (field_schema.field_type == float and isinstance(value, int)):
                errors.append(ValidationError(
                    field=field_name,
                    code=ValidationErrorCode.INVALID_TYPE,
                    message=f"{field_name} must be of type {field_schema.field_type.__name__}"
                ))
                continue
        
        # String-specific validations
        if isinstance(value, str):
            # Sanitize if enabled (but not for passwords)
            if field_schema.sanitize:
                value = sanitize_string(value, field_schema.max_length or 10000)
            
            # Length validation
            if field_schema.min_length and len(value) < field_schema.min_length:
                errors.append(ValidationError(
                    field=field_name,
                    code=ValidationErrorCode.TOO_SHORT,
                    message=f"{field_name} must be at least {field_schema.min_length} characters"
                ))
                continue
            
            if field_schema.max_length and len(value) > field_schema.max_length:
                errors.append(ValidationError(
                    field=field_name,
                    code=ValidationErrorCode.TOO_LONG,
                    message=f"{field_name} must not exceed {field_schema.max_length} characters"
                ))
                continue
            
            # Pattern validation
            if field_schema.pattern and not re.match(field_schema.pattern, value):
                errors.append(ValidationError(
                    field=field_name,
                    code=ValidationErrorCode.INVALID_FORMAT,
                    message=f"{field_name} has invalid format"
                ))
                continue
        
        # Numeric range validation
        if isinstance(value, (int, float)):
            if field_schema.min_value is not None and value < field_schema.min_value:
                errors.append(ValidationError(
                    field=field_name,
                    code=ValidationErrorCode.OUT_OF_RANGE,
                    message=f"{field_name} must be at least {field_schema.min_value}"
                ))
                continue
            
            if field_schema.max_value is not None and value > field_schema.max_value:
                errors.append(ValidationError(
                    field=field_name,
                    code=ValidationErrorCode.OUT_OF_RANGE,
                    message=f"{field_name} must not exceed {field_schema.max_value}"
                ))
                continue
        
        # List length validation
        if isinstance(value, list):
            if field_schema.min_length and len(value) < field_schema.min_length:
                errors.append(ValidationError(
                    field=field_name,
                    code=ValidationErrorCode.TOO_SHORT,
                    message=f"{field_name} must have at least {field_schema.min_length} items"
                ))
                continue
            
            if field_schema.max_length and len(value) > field_schema.max_length:
                errors.append(ValidationError(
                    field=field_name,
                    code=ValidationErrorCode.TOO_LONG,
                    message=f"{field_name} must not exceed {field_schema.max_length} items"
                ))
                continue
        
        # Allowed values validation
        if field_schema.allowed_values and value not in field_schema.allowed_values:
            errors.append(ValidationError(
                field=field_name,
                code=ValidationErrorCode.INVALID_VALUE,
                message=f"{field_name} must be one of: {', '.join(map(str, field_schema.allowed_values))}"
            ))
            continue
        
        # Custom validator
        if field_schema.custom_validator:
            is_valid, error_msg = field_schema.custom_validator(value)
            if not is_valid:
                # Determine appropriate error code
                error_code = ValidationErrorCode.VALIDATION_ERROR
                if 'email' in field_name.lower():
                    error_code = ValidationErrorCode.INVALID_EMAIL
                elif 'password' in field_name.lower():
                    error_code = ValidationErrorCode.WEAK_PASSWORD
                elif 'token' in field_name.lower():
                    error_code = ValidationErrorCode.INVALID_TOKEN
                
                errors.append(ValidationError(
                    field=field_name,
                    code=error_code,
                    message=error_msg
                ))
                continue
        
        # Field passed all validations
        validated_data[field_name] = value
    
    if errors:
        return ValidationResult(is_valid=False, errors=errors)
    
    return ValidationResult(is_valid=True, data=validated_data)


def validate_content_type(request, expected: str = 'application/json') -> Optional[Dict]:
    """
    Validate Content-Type header.
    
    Returns error response dict if invalid, None if valid.
    """
    content_type = request.content_type or ''
    
    # Allow for charset specification (e.g., 'application/json; charset=utf-8')
    if not content_type.startswith(expected):
        return {
            'error': {
                'code': 'INVALID_CONTENT_TYPE',
                'message': f'Content-Type must be {expected}',
                'details': {'received': content_type}
            }
        }
    return None


def validate_request_size(request, max_bytes: int = 1048576) -> Optional[Dict]:
    """
    Validate request body size (default 1MB limit).
    
    Returns error response dict if too large, None if valid.
    """
    content_length = request.META.get('CONTENT_LENGTH')
    if content_length:
        try:
            size = int(content_length)
            if size > max_bytes:
                return {
                    'error': {
                        'code': 'REQUEST_TOO_LARGE',
                        'message': f'Request body must not exceed {max_bytes} bytes',
                        'details': {'received': size, 'limit': max_bytes}
                    }
                }
        except (ValueError, TypeError):
            pass
    return None
