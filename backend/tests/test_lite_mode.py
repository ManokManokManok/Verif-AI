import json
from unittest.mock import MagicMock, patch

import pytest

from src.infrastructure.ai.loaders import lite_mode
from src.use_cases.ai.gemini_classification import GeminiClassificationUseCase


@pytest.mark.parametrize('value,expected', [
    ('true', True), ('1', True), ('YES', True), ('on', True),
    ('false', False), ('', False), ('nope', False),
])
def test_lite_mode_env(monkeypatch, value, expected):
    monkeypatch.setenv('LITE_MODE', value)
    assert lite_mode() is expected


def test_lite_mode_default_off(monkeypatch):
    monkeypatch.delenv('LITE_MODE', raising=False)
    assert lite_mode() is False


def test_parse_scam_over_threshold():
    raw = json.dumps({
        'scam_score': 85, 'scam_type': 'Not A Real Type', 'type_confidence': 120,
        'summary': 'Looks fake.', 'key_markers': ['a', ' ', 'b'],
    })
    result = GeminiClassificationUseCase.parse_response(raw, 50)
    assert result['is_scam'] is True
    assert result['label'] == 'Scam'
    assert result['scam_type'] == 'Mobile and Digital'
    assert result['type_confidence'] == 100.0
    assert result['key_markers'] == ['a', 'b']
    assert result['legit_score'] == 15.0


def test_parse_clamps_and_legit():
    result = GeminiClassificationUseCase.parse_response(json.dumps({'scam_score': -20}), 50)
    assert result['scam_score'] == 0.0
    assert result['is_scam'] is False
    assert result['scam_type'] is None
    assert result['summary']


@pytest.mark.parametrize('score,expected', [(39, 39.0), (40, 60.0), (50, 65.0), (59, 65.0), (60, 60.0)])
def test_parse_avoids_fence_sitting(score, expected):
    result = GeminiClassificationUseCase.parse_response(json.dumps({'scam_score': score}), 50)
    assert result['scam_score'] == expected


def test_low_scores_default_to_zero():
    for score, expected in [(1.4, 0.0), (15, 0.0), (20, 0.0), (20.5, 20.5)]:
        result = GeminiClassificationUseCase.parse_response(json.dumps({'scam_score': score}), 50)
        assert result['scam_score'] == expected
        assert result['legit_score'] == 100.0 - expected
        assert result['is_scam'] is False


def test_percentages_follow_the_displayed_low_score():
    raw = json.dumps({'scam_score': 12.4, 'summary': 'Only 12% risk.', 'score_explanation': 'About 88% legit.'})
    result = GeminiClassificationUseCase.parse_response(raw, 50)
    assert result['summary'] == 'Only 0% risk.'
    assert result['score_explanation'] == 'About 100% legit.'


def test_bare_and_unit_forms_of_the_raw_score_are_rewritten():
    raw = json.dumps({
        'scam_score': 1.25,
        'summary': 'It scored 1.25 out of 100 here.',
        'score_explanation': 'A score of 1.25 reflects minimal risk; the risk is 1.25%, or 1.25/100. It has 1 pickup point and 2 steps.',
        'key_markers': ['Risk score 1.25'],
    })
    result = GeminiClassificationUseCase.parse_response(raw, 50)
    assert '1.25' not in json.dumps(result)
    assert result['summary'] == 'It scored 0 out of 100 here.'
    assert result['score_explanation'].startswith('A score of 0 reflects minimal risk; the risk is 0%, or 0/100.')
    assert '1 pickup point and 2 steps' in result['score_explanation']


def test_percentages_in_prose_match_exact_score():
    raw = json.dumps({'scam_score': 85.5, 'summary': 'Likelihood is 86% scam.',
                      'score_explanation': 'About 86% risk, and 14% legit, 40% unrelated.'})
    result = GeminiClassificationUseCase.parse_response(raw, 50)
    assert result['summary'] == 'Likelihood is 85.5% scam.'
    assert result['score_explanation'] == 'About 85.5% risk, and 14.5% legit, 40% unrelated.'


def test_parse_rejects_non_object():
    with pytest.raises(ValueError):
        GeminiClassificationUseCase.parse_response('[1]')


def test_detect_uses_provider(monkeypatch):
    provider = MagicMock()
    provider.create_structured_completion.return_value = json.dumps({'scam_score': 10})
    result = GeminiClassificationUseCase(provider).detect('hello, 20% off today')
    assert result['is_scam'] is False
    assert provider.create_structured_completion.called


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
    assert guest_limits.claim_guest_use('sess-lite-test', 'f') is True
    assert guest_limits.claim_guest_use('sess-lite-test', 'f') is False
    guest_limits.release_guest_use('sess-lite-test', 'f')
    assert guest_limits.claim_guest_use('sess-lite-test', 'f') is True
    guest_limits.release_guest_use('sess-lite-test', 'f')
