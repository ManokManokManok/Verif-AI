import runpy
from pathlib import Path

import pytest

from src.domain.services import MFACodeGenerator, TokenGenerator


def test_verification_token_ignores_old_fixed_token_switch(monkeypatch):
    monkeypatch.setenv('BYPASS_VERIFICATION_CODE', '1')
    monkeypatch.setattr('src.domain.services.secrets.token_hex', lambda length: 'a' * (2 * length))

    assert TokenGenerator.generate_verification_token() == 'a' * 32


def test_mfa_generator_ignores_old_fixed_code_switch(monkeypatch):
    monkeypatch.setenv('BYPASS_MFA_CODE', '1')
    monkeypatch.setattr('src.domain.services.secrets.choice', lambda digits: '7')

    assert MFACodeGenerator.generate_code() == '777777'


def load_settings(monkeypatch, debug, mfa):
    monkeypatch.setattr('dotenv.load_dotenv', lambda *args, **kwargs: None)
    monkeypatch.setenv('DJANGO_SECRET_KEY', 'test-key')
    monkeypatch.setenv('DJANGO_ALLOWED_HOSTS', 'localhost')
    monkeypatch.setenv('DJANGO_DEBUG', debug)
    if mfa is None:
        monkeypatch.delenv('MFA_ENABLED', raising=False)
    else:
        monkeypatch.setenv('MFA_ENABLED', mfa)
    settings_path = Path(__file__).resolve().parents[1] / 'verfai' / 'settings.py'
    return runpy.run_path(str(settings_path))


def test_mfa_is_enabled_by_default(monkeypatch):
    assert load_settings(monkeypatch, 'false', None)['MFA_ENABLED'] is True


def test_mfa_cannot_be_disabled_outside_debug_mode(monkeypatch):
    with pytest.raises(ValueError, match='MFA_ENABLED cannot be disabled'):
        load_settings(monkeypatch, 'false', 'false')


def test_development_can_explicitly_disable_mfa(monkeypatch):
    assert load_settings(monkeypatch, 'true', 'false')['MFA_ENABLED'] is False


def test_login_internal_error_does_not_expose_exception(monkeypatch, caplog):
    import os
    import django

    monkeypatch.setenv('RATE_LIMIT_ENABLED', 'false')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'verfai.settings')
    django.setup()

    from rest_framework.test import APIRequestFactory
    from src.interfaces.rest import views

    def fail():
        raise RuntimeError('private diagnostic detail')

    monkeypatch.setattr(views, 'get_user_repository', fail)
    request = APIRequestFactory().post(
        '/api/auth/login/',
        {'email': 'user@example.com', 'password': 'valid-password'},
        format='json',
    )

    response = views.login(request)

    assert response.status_code == 500
    assert response.data['error']['message'] == 'An unexpected error occurred'
    assert 'Login failed unexpectedly' in caplog.text
