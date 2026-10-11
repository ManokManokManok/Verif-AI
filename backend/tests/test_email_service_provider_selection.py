import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_dir))

from src.infrastructure import email_service as email_module


class _DummyProvider:
    def send_verification_email(self, email: str, token: str) -> bool:
        return True

    def send_password_reset_email(self, email: str, token: str) -> bool:
        return True

    def send_mfa_code_email(self, email: str, code: str) -> bool:
        return True


def test_email_backend_defaults_to_mock(monkeypatch):
    monkeypatch.delenv('EMAIL_BACKEND', raising=False)
    email_module.reset_email_service()
    service = email_module.get_email_service()
    assert isinstance(service, email_module.MockEmailService)


def test_factory_selects_sendgrid_without_breaking_existing_provider(monkeypatch):
    monkeypatch.setenv('EMAIL_BACKEND', 'sendgrid')

    class _SendGridStub(_DummyProvider):
        pass

    monkeypatch.setattr(email_module, 'SendGridEmailService', _SendGridStub)
    email_module.reset_email_service()
    service = email_module.get_email_service()
    assert isinstance(service, _SendGridStub)


def test_factory_selects_nodemailer_provider(monkeypatch):
    monkeypatch.setenv('EMAIL_BACKEND', 'nodemailer')

    class _NodeMailerStub(_DummyProvider):
        pass

    monkeypatch.setattr(email_module, 'NodeMailerEmailService', _NodeMailerStub)
    email_module.reset_email_service()
    service = email_module.get_email_service()
    assert isinstance(service, _NodeMailerStub)


def test_smtp_uses_configured_gmail_for_sender_and_login(monkeypatch):
    monkeypatch.setenv('EMAIL_HOST', 'smtp.gmail.com')
    monkeypatch.setenv('EMAIL_PORT', '587')
    monkeypatch.setenv('EMAIL_USE_TLS', 'True')
    monkeypatch.setenv('EMAIL_HOST_USER', 'verifaisupportacc@gmail.com')
    monkeypatch.setenv('EMAIL_HOST_PASSWORD', 'test-app-password')
    monkeypatch.delenv('EMAIL_FROM_ADDRESS', raising=False)

    service = email_module.SMTPEmailService()

    assert service.host == 'smtp.gmail.com'
    assert service.port == 587
    assert service.use_tls is True
    assert service.username == 'verifaisupportacc@gmail.com'
    assert service.from_address == 'verifaisupportacc@gmail.com'


def test_transactional_email_templates_include_clear_instructions_and_security_help(monkeypatch):
    monkeypatch.setenv('VERIFAI_SUPPORT_EMAIL', 'support@example.com')
    templates = [
        (email_module._password_reset_code_html('123456'), '10 minutes'),
        (email_module._mfa_code_html('123456'), '5 minutes'),
        (email_module._password_change_code_html('123456'), '5 minutes'),
        (email_module._email_verification_code_html('123456'), '15 minutes'),
    ]

    for html, expiry in templates:
        assert 'How to use your code' in html
        assert 'use the newest email' in html
        assert f'Expires in {expiry}' in html
        assert 'do not share or forward the code' in html
        assert 'mailto:support@example.com' in html
        assert '123456' in html


def test_transactional_email_templates_escape_codes_and_links():
    html = email_module._mfa_code_html('<img src=x onerror=alert(1)>')
    verification_html = email_module._verification_html(
        'https://example.com/verify?token="><script>alert(1)</script>'
    )

    assert '<img src=x onerror=alert(1)>' not in html
    assert '&lt;img src=x onerror=alert(1)&gt;' in html
    assert '<script>alert(1)</script>' not in verification_html
    assert '&lt;script&gt;alert(1)&lt;/script&gt;' in verification_html


def test_nodemailer_send_calls_node_bridge(monkeypatch, tmp_path):
    script = tmp_path / 'nodemailer_sender.js'
    script.write_text('console.log("ok")', encoding='utf-8')

    monkeypatch.setenv('NODE_EXECUTABLE', 'node')
    monkeypatch.setenv('NODEMAILER_SCRIPT_PATH', str(script))
    monkeypatch.setenv('NODEMAILER_TIMEOUT_SECONDS', '5')
    monkeypatch.setenv('NODEMAILER_HOST', 'smtp.example.com')
    monkeypatch.setenv('NODEMAILER_PORT', '587')
    monkeypatch.setenv('NODEMAILER_SECURE', 'False')
    monkeypatch.setenv('NODEMAILER_USER', 'user@example.com')
    monkeypatch.setenv('NODEMAILER_PASS', 'app-password')

    monkeypatch.setattr(email_module.shutil, 'which', lambda _: '/usr/bin/node')

    captured = {}

    def _fake_run(command, input, text, capture_output, timeout, check):
        captured['command'] = command
        captured['input'] = input

        class _Result:
            returncode = 0
            stderr = ''

        return _Result()

    monkeypatch.setattr(email_module.subprocess, 'run', _fake_run)

    provider = email_module.NodeMailerEmailService()
    sent = provider.send_mfa_code_email('recipient@example.com', '123456')

    assert sent is True
    assert captured['command'][0] == 'node'
    assert 'recipient@example.com' in captured['input']


def test_nodemailer_empty_host_falls_back_to_email_host(monkeypatch, tmp_path):
    script = tmp_path / 'nodemailer_sender.js'
    script.write_text('console.log("ok")', encoding='utf-8')

    monkeypatch.setenv('NODE_EXECUTABLE', 'node')
    monkeypatch.setenv('NODEMAILER_SCRIPT_PATH', str(script))
    monkeypatch.setenv('NODEMAILER_HOST', '')
    monkeypatch.setenv('EMAIL_HOST', 'smtp.gmail.com')
    monkeypatch.setenv('NODEMAILER_PORT', '587')
    monkeypatch.setenv('NODEMAILER_SECURE', 'False')
    monkeypatch.setenv('NODEMAILER_USER', 'user@example.com')
    monkeypatch.setenv('NODEMAILER_PASS', 'app-password')

    monkeypatch.setattr(email_module.shutil, 'which', lambda _: '/usr/bin/node')

    captured = {}

    def _fake_run(command, input, text, capture_output, timeout, check):
        captured['input'] = input

        class _Result:
            returncode = 0
            stderr = ''

        return _Result()

    monkeypatch.setattr(email_module.subprocess, 'run', _fake_run)

    provider = email_module.NodeMailerEmailService()
    sent = provider.send_mfa_code_email('recipient@example.com', '123456')

    assert sent is True
    assert 'smtp.gmail.com' in captured['input']
