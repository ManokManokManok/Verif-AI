import os
from types import SimpleNamespace
from unittest.mock import MagicMock

import django
import pytest

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'verfai.settings')
django.setup()

from rest_framework.test import APIRequestFactory
from src.interfaces.rest import views


MESSAGE = 'Your account is locked. Please verify your details now.'
BERT_RESULT = {
    'scam_score': 81.25,
    'legit_score': 18.75,
    'is_scam': True,
    'label': 'Scam',
    'scam_type': 'Mobile and Digital',
    'type_confidence': 90.0,
}


@pytest.fixture
def pipeline(monkeypatch):
    monkeypatch.setenv('RATE_LIMIT_ENABLED', 'false')
    provider = object()
    gate = MagicMock()
    gate.evaluate.return_value = {'route': 'analyze'}
    loader = MagicMock(return_value=('tokenizer', 'model', {0: 'Mobile and Digital'}))
    detector = MagicMock()
    detector.detect.return_value = BERT_RESULT.copy()
    explanation = MagicMock()
    explanation.analyze.return_value = {'summary': 'Explanation', 'key_markers': ['Urgency']}
    repository = MagicMock()
    repository.save.side_effect = lambda analysis: analysis
    monkeypatch.setattr(views, 'get_genai_provider', lambda: provider)
    monkeypatch.setattr(views, 'GatekeeperUseCase', MagicMock(return_value=gate))
    monkeypatch.setattr(views, 'load_multihead_model', loader)
    monkeypatch.setattr(views, 'ScamDetectionUseCase', MagicMock(return_value=detector))
    monkeypatch.setattr(views, 'LLMAnalysisUseCase', MagicMock(return_value=explanation))
    monkeypatch.setattr(views, 'get_analysis_repository', lambda: repository)
    monkeypatch.setattr(views, 'check_confidence', lambda **kwargs: SimpleNamespace(needs_review=False, review_reason=None))
    return SimpleNamespace(gate=gate, loader=loader, detector=detector,
                           explanation=explanation, repository=repository)


def request_detection():
    request = APIRequestFactory().post('/api/detect-scam/', {'message': MESSAGE}, format='json')
    return views.detect_scam(request)


def test_analyze_route_uses_bert_then_generates_explanation_and_saves(pipeline):
    response = request_detection()

    assert response.status_code == 200
    pipeline.gate.evaluate.assert_called_once_with(MESSAGE)
    pipeline.loader.assert_called_once_with()
    pipeline.detector.detect.assert_called_once_with(MESSAGE)
    pipeline.explanation.analyze.assert_called_once_with(MESSAGE, BERT_RESULT)
    assert response.data['scam_score'] == BERT_RESULT['scam_score']
    assert response.data['summary'] == 'Explanation'
    assert response.data['ref_id']
    assert 'jwt_debug' not in response.data
    saved = pipeline.repository.save.call_args.args[0]
    assert saved.analyzer_type == 'bert'
    assert saved.analyzer_version == 'v1'
    assert saved.scam_score == BERT_RESULT['scam_score']


def test_authenticated_detection_omits_jwt_debug(pipeline, monkeypatch):
    jwt_service = SimpleNamespace(verify_access_token=lambda token: {'user_id': 'user-123'})
    user_repo = SimpleNamespace(get_by_id=lambda user_id: SimpleNamespace(id=user_id))
    monkeypatch.setattr(views, 'get_jwt_service', lambda: jwt_service)
    monkeypatch.setattr(views, 'get_user_repository', lambda: user_repo)
    request = APIRequestFactory().post(
        '/api/detect/', {'message': MESSAGE}, format='json',
        HTTP_AUTHORIZATION='Bearer test-token',
    )

    response = views.detect_scam(request)

    assert response.status_code == 200
    assert 'jwt_debug' not in response.data
    assert pipeline.repository.save.call_args.args[0].user_id == 'user-123'


@pytest.mark.parametrize('route', ['limited', 'rejected'])
def test_gatekeeper_stops_before_classifier(pipeline, route):
    pipeline.gate.evaluate.return_value = {'route': route, 'reason_code': 'too_vague'}

    response = request_detection()

    assert response.status_code == 200
    assert response.data['result_type'] == 'gatekeeper'
    assert response.data['route'] == route
    pipeline.loader.assert_not_called()
    pipeline.detector.detect.assert_not_called()
    pipeline.explanation.analyze.assert_not_called()
    pipeline.repository.save.assert_not_called()


def test_obsolete_gatekeeper_bypass_setting_does_not_skip_screening(pipeline, monkeypatch):
    monkeypatch.setenv('GATEKEEPER_DISABLED', 'true')
    pipeline.gate.evaluate.return_value = {'route': 'rejected', 'reason_code': 'too_vague'}

    response = request_detection()

    assert response.status_code == 200
    assert response.data['route'] == 'rejected'
    pipeline.gate.evaluate.assert_called_once_with(MESSAGE)
    pipeline.loader.assert_not_called()


@pytest.mark.parametrize('unavailable', ['exception', 'missing_model', 'missing_tokenizer'])
def test_model_unavailable_returns_service_error_without_classifying(pipeline, unavailable):
    if unavailable == 'exception':
        pipeline.loader.side_effect = RuntimeError('model missing')
    elif unavailable == 'missing_model':
        pipeline.loader.return_value = ('tokenizer', None, {})
    else:
        pipeline.loader.return_value = (None, 'model', {})

    response = request_detection()

    assert response.status_code == 503
    assert response.data['error']['code'] == 'MODEL_NOT_LOADED'
    pipeline.detector.detect.assert_not_called()
    pipeline.explanation.analyze.assert_not_called()
    pipeline.repository.save.assert_not_called()
