import os
import unittest
from unittest.mock import patch

from src.infrastructure.ai.genai_provider import GenAIProvider


class _FakeProvider:
    def __init__(self, response=None, error=None, model_name='fake-model'):
        self.response = response or {"choices": [{"message": {"content": "ok"}}]}
        self.error = error
        self.calls = 0
        self.model_name = model_name

    def create_chat_completion(self, **_options):
        self.calls += 1
        if self.error:
            raise self.error
        return self.response

    def create_structured_completion(self, **_options):
        self.calls += 1
        if self.error:
            raise self.error
        return self.response


class _TransientError(Exception):
    status_code = 503


class _PermanentError(Exception):
    status_code = 400


class GenAIProviderTests(unittest.TestCase):
    def test_structured_request_tries_fallback_model_on_transient_failure(self):
        primary = _FakeProvider(error=_TransientError('busy'), model_name='primary')
        first_fallback = _FakeProvider(error=_TransientError('still busy'), model_name='first-fallback')
        second_fallback = _FakeProvider(response='{"ok":true}', model_name='second-fallback')
        provider = GenAIProvider(gemini_provider=primary)
        provider.gemini_fallback_models = ['first-fallback', 'second-fallback']
        provider.gemini_fallbacks = {
            'first-fallback': first_fallback,
            'second-fallback': second_fallback,
        }

        result = provider.create_structured_completion(messages=[], response_schema={})

        self.assertEqual(result, '{"ok":true}')
        self.assertEqual(primary.calls, 1)
        self.assertEqual(first_fallback.calls, 1)
        self.assertEqual(second_fallback.calls, 1)

    def test_structured_request_does_not_try_fallback_on_permanent_failure(self):
        primary = _FakeProvider(error=_PermanentError('invalid request'), model_name='primary')
        fallback = _FakeProvider(response='{"ok":true}', model_name='fallback')
        provider = GenAIProvider(gemini_provider=primary)
        provider.gemini_fallback_models = ['fallback']
        provider.gemini_fallbacks = {'fallback': fallback}

        with self.assertRaises(_PermanentError):
            provider.create_structured_completion(messages=[], response_schema={})

        self.assertEqual(fallback.calls, 0)

    def test_gemini_success_does_not_load_or_call_gemma(self):
        gemini = _FakeProvider()
        gemma_loader = unittest.mock.Mock()
        provider = GenAIProvider(gemini_provider=gemini, gemma_loader=gemma_loader)

        result = provider.create_chat_completion(messages=[])

        self.assertEqual(result["choices"][0]["message"]["content"], "ok")
        gemma_loader.assert_not_called()
        self.assertEqual(gemini.calls, 1)

    def test_gemini_failure_falls_back_to_gemma(self):
        gemini = _FakeProvider(error=RuntimeError("quota"))
        gemma = _FakeProvider(response={"choices": [{"message": {"content": "fallback"}}]})
        gemma_loader = unittest.mock.Mock(return_value=gemma)
        provider = GenAIProvider(gemini_provider=gemini, gemma_loader=gemma_loader)

        result = provider.create_chat_completion(messages=[])

        self.assertEqual(result["choices"][0]["message"]["content"], "fallback")
        gemma_loader.assert_called_once_with()
        self.assertEqual(gemma.calls, 1)

    def test_without_gemini_gemma_is_loaded_on_demand(self):
        gemma = _FakeProvider()
        gemma_loader = unittest.mock.Mock(return_value=gemma)
        with patch.dict(os.environ, {"GEMINI_API_KEY": ""}, clear=False):
            provider = GenAIProvider(gemini_provider=None, gemma_loader=gemma_loader)
            provider.create_chat_completion(messages=[])

        gemma_loader.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
