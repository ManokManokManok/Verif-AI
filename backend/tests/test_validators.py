"""
Tests for input validation and sanitization utilities.

Run: pytest backend/tests/test_validators.py -v
"""
import os
import sys

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.infrastructure.validators import (
    FieldType,
    RequestValidator,
    sanitize_string,
    validate_email,
    validate_password,
    get_signup_validator,
    get_detect_scam_validator,
)


class TestPrimitiveValidators:
    def test_validate_email_accepts_valid_format(self):
        is_valid, error = validate_email("user@example.com")
        assert is_valid is True
        assert error is None

    def test_validate_email_rejects_invalid_format(self):
        is_valid, error = validate_email("not-an-email")
        assert is_valid is False
        assert error == "Invalid email format"

    def test_validate_password_rejects_missing_requirements(self):
        is_valid, errors = validate_password("weak")
        assert is_valid is False
        assert any("at least 8 characters" in err for err in errors)
        assert any("uppercase" in err for err in errors)
        assert any("digit" in err for err in errors)

    def test_validate_password_rejects_whitespace(self):
        is_valid, errors = validate_password("Abcdef1! withspace")
        assert is_valid is False
        assert any("must not contain spaces or whitespace" in err for err in errors)

    def test_sanitize_string_escapes_html(self):
        raw = '<script>alert("x")</script>'
        cleaned = sanitize_string(raw)
        assert "<script>" not in cleaned
        assert "&lt;script&gt;" in cleaned


class TestRequestValidator:
    def test_rejects_unknown_fields_by_default(self):
        validator = RequestValidator().add_field("email", FieldType.EMAIL, required=True)

        is_valid, errors, cleaned = validator.validate({
            "email": "user@example.com",
            "unexpected": "value",
        })

        assert is_valid is False
        assert "_unexpected" in errors
        assert cleaned["email"] == "user@example.com"

    def test_signup_validator_normalizes_email_and_validates_fields(self):
        validator = get_signup_validator()

        is_valid, errors, cleaned = validator.validate({
            "email": "USER@EXAMPLE.COM",
            "username": "valid_user-1",
            "password": "StrongPass1!",
        })

        assert is_valid is True
        assert errors == {}
        assert cleaned["email"] == "user@example.com"
        assert cleaned["username"] == "valid_user-1"

    def test_detect_scam_validator_rejects_empty_message(self):
        validator = get_detect_scam_validator()

        is_valid, errors, _ = validator.validate({"message": ""})

        assert is_valid is False
        assert "message" in errors
