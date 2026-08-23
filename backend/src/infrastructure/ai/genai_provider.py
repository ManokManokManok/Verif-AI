"""Gemini-first generative AI provider with local Gemma fallback."""

import logging
import os
from typing import Any, Callable, Dict, List, Optional

from .loaders import load_gemma_model

logger = logging.getLogger(__name__)


def _safe_error_detail(error: Exception) -> str:
    detail = str(error)
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        detail = detail.replace(api_key, "[REDACTED]")
    return detail[:500]


class GeminiProvider:
    """Adapt Google's Gemini API to the existing chat-completion contract."""

    def __init__(self, api_key: str, model_name: str):
        from google import genai  # type: ignore

        self.model_name = model_name
        self.client = genai.Client(api_key=api_key)

    def create_chat_completion(self, messages: List[Dict[str, str]], **options: Any) -> Dict[str, Any]:
        from google.genai import types  # type: ignore

        system_parts = [item["content"] for item in messages if item.get("role") == "system"]
        contents = []
        for item in messages:
            role = item.get("role")
            if role == "system":
                continue
            contents.append({
                "role": "model" if role == "assistant" else "user",
                "parts": [{"text": item.get("content", "")}],
            })

        config = types.GenerateContentConfig(
            system_instruction="\n\n".join(system_parts) or None,
            max_output_tokens=options.get("max_tokens"),
            temperature=options.get("temperature"),
            top_p=options.get("top_p"),
            stop_sequences=self._stop_sequences(options.get("stop")),
            thinking_config=types.ThinkingConfig(thinking_level="MINIMAL"),
        )
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=contents,
            config=config,
        )
        text = getattr(response, "text", None)
        if not text or not text.strip():
            raise RuntimeError("Gemini returned an empty response")
        return {"choices": [{"message": {"content": text}}]}

    @staticmethod
    def _stop_sequences(value: Any) -> Optional[List[str]]:
        if not value:
            return None
        return [item for item in value if item and not item.startswith("<|")]


class GenAIProvider:
    """Use Gemini first, then lazily load and use Gemma only after failure."""

    def __init__(self, gemini_provider: Optional[Any] = None, gemma_loader: Callable[[], Any] = load_gemma_model):
        self.gemma_loader = gemma_loader
        self.gemini = gemini_provider
        self.gemini_configured = bool(os.getenv("GEMINI_API_KEY"))

        if self.gemini is None and self.gemini_configured and self._gemini_enabled():
            try:
                self.gemini = GeminiProvider(
                    api_key=os.environ["GEMINI_API_KEY"],
                    model_name=os.getenv("GEMINI_MODEL", "gemini-3.6-flash"),
                )
                logger.info("[GEMINI] Available: true; model=%s", os.getenv("GEMINI_MODEL", "gemini-3.6-flash"))
            except Exception as exc:
                logger.warning("[GEMINI] Available: false; initialization failed: %s", type(exc).__name__)
        elif not self.gemini_configured:
            logger.warning("[GEMINI] Available: false; GEMINI_API_KEY is not configured")
        elif not self._gemini_enabled():
            logger.info("[GEMINI] Available: false; disabled by configuration")

    def create_chat_completion(self, messages: List[Dict[str, str]], **options: Any) -> Dict[str, Any]:
        if self.gemini is not None:
            try:
                response = self.gemini.create_chat_completion(messages=messages, **options)
                logger.warning("[GENAI] Provider used: GEMINI")
                return response
            except Exception as exc:
                logger.warning(
                    "[GEMINI] Request failed: %s; %s; falling back to Gemma",
                    type(exc).__name__,
                    _safe_error_detail(exc),
                )

        gemma = self.gemma_loader()
        response = gemma.create_chat_completion(messages=messages, **options)
        logger.warning("[GENAI] Provider used: GEMMA_FALLBACK")
        return response

    @staticmethod
    def _gemini_enabled() -> bool:
        return os.getenv("GEMINI_ENABLED", "true").lower() in ("1", "true", "yes")


_provider: Optional[GenAIProvider] = None


def get_genai_provider() -> GenAIProvider:
    """Return the shared Gemini-first provider without warming Gemma."""
    global _provider
    if _provider is None:
        _provider = GenAIProvider()
    return _provider


def genai_status() -> Dict[str, Any]:
    provider = get_genai_provider()
    return {
        "gemini_configured": provider.gemini_configured,
        "gemini_available": provider.gemini is not None,
        "gemini_model": os.getenv("GEMINI_MODEL", "gemini-3.6-flash"),
    }
