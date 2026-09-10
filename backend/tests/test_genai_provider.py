import os
import unittest
from unittest.mock import patch

from src.infrastructure.ai.genai_provider import GenAIProvider


class _FakeProvider:
    def __init__(self, response=None, error=None):
        self.response = response or {"choices": [{"message": {"content": "ok"}}]}
        self.error = error
        self.calls = 0

    def create_chat_completion(self, **_options):
        self.calls += 1
        if self.error:
            raise self.error
        return self.response


class GenAIProviderTests(unittest.TestCase):
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
