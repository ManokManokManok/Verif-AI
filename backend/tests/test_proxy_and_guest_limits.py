from unittest.mock import MagicMock


def test_xff_trusted_hops(monkeypatch):
    from src.infrastructure.rate_limiter import get_client_ip
    request = MagicMock()
    request.META = {'HTTP_X_FORWARDED_FOR': '6.6.6.6, 1.2.3.4, 10.0.0.1', 'REMOTE_ADDR': '10.0.0.1'}
    monkeypatch.setenv('TRUSTED_PROXY_HOPS', '0')
    assert get_client_ip(request) == '6.6.6.6'
    monkeypatch.setenv('TRUSTED_PROXY_HOPS', '1')
    assert get_client_ip(request) == '10.0.0.1'
    monkeypatch.setenv('TRUSTED_PROXY_HOPS', '2')
    assert get_client_ip(request) == '1.2.3.4'


def test_guest_limit_memory(monkeypatch):
    from src.apps.chatbot import guest_limits
    monkeypatch.setenv('RATE_LIMIT_BACKEND', 'memory')
    assert guest_limits.claim_guest_use('sess-test', 'f') is True
    assert guest_limits.claim_guest_use('sess-test', 'f') is False
    guest_limits.release_guest_use('sess-test', 'f')
    assert guest_limits.claim_guest_use('sess-test', 'f') is True
    guest_limits.release_guest_use('sess-test', 'f')
