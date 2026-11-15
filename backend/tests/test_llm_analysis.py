import json
from unittest.mock import MagicMock

from src.use_cases.ai.llm_analysis import LLMAnalysisUseCase


def test_guidance_preserves_missing_context():
    provider = MagicMock()
    provider.create_structured_completion.return_value = json.dumps({
        'score_explanation': 'The message asks you to verify your account.',
        'missing_context': ['Whether you expected this message'],
        'suggested_action': 'Use the official app.',
        'avoid': ['Do not use the link.'],
    })

    result = LLMAnalysisUseCase(provider)._get_guidance('Verify your account', {'scam_score': 81.25})

    assert result['missing_context'] == ['Whether you expected this message']
    assert result['suggested_action'] == 'Use the official app.'
    schema = provider.create_structured_completion.call_args.kwargs['response_schema']
    assert 'missing_context' in schema['required']


def test_guidance_failure_includes_empty_missing_context():
    provider = MagicMock()
    provider.create_structured_completion.side_effect = RuntimeError('unavailable')

    result = LLMAnalysisUseCase(provider)._get_guidance('Verify your account', {'scam_score': 81.25})

    assert result['missing_context'] == []
