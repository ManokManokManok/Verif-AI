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

