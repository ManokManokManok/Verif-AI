"""Discover and probe Gemini text-generation models for the configured API key.

Run from the repository root:
    python backend/scripts/check_gemini_models.py

The default mode only lists models exposed by the API catalog. Use --probe to
send a small structured request to each text-generation model. Probing consumes
API requests, so it is always opt-in.
"""

import argparse
import os
import sys
from typing import Any, Iterable

from dotenv import load_dotenv


EXCLUDED_MODEL_MARKERS = (
    "-audio",
    "-computer-use",
    "-image",
    "-live",
    "-tts",
    "deep-research",
    "embedding",
    "lyria",
    "nano-banana",
    "robotics",
    "transcribe",
    "veo-",
)


def _is_text_generation_model(model: Any) -> bool:
    name = str(getattr(model, "name", "")).lower()
    methods = getattr(model, "supported_actions", None) or getattr(model, "supported_generation_methods", None) or []
    return (
        bool(name)
        and "generatecontent" in {str(method).lower() for method in methods}
        and not any(marker in name for marker in EXCLUDED_MODEL_MARKERS)
    )


def _short_error(error: Exception) -> str:
    detail = str(error).replace("\n", " ")
    return f"{type(error).__name__}: {detail[:240]}"


def _probe(client: Any, model_name: str) -> tuple[str, str]:
    from google.genai import types

    try:
        response = client.models.generate_content(
            model=model_name,
            contents="Return JSON with the boolean field ok set to true.",
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema={
                    "type": "object",
                    "properties": {"ok": {"type": "boolean"}},
                    "required": ["ok"],
                },
                max_output_tokens=64,
                temperature=0,
            ),
        )
        text = getattr(response, "text", None)
        if text and text.strip():
            return "working", text.strip().replace("\n", " ")[:120]
        finish_reason = None
        candidates = getattr(response, "candidates", None) or []
        if candidates:
            finish_reason = getattr(candidates[0], "finish_reason", None)
        return "empty_response", str(finish_reason or "no text")
    except Exception as error:
        detail = _short_error(error)
        lowered = detail.lower()
        if "503" in lowered or "unavailable" in lowered or "high demand" in lowered:
            return "capacity_unavailable", detail
        if "404" in lowered or "not_found" in lowered or "no longer available" in lowered:
            return "not_available_to_account", detail
        if "429" in lowered or "quota" in lowered or "rate" in lowered:
            return "rate_limited", detail
        return "failed", detail


def _catalog_models(client: Any) -> Iterable[Any]:
    return sorted(
        (model for model in client.models.list() if _is_text_generation_model(model)),
        key=lambda model: str(getattr(model, "name", "")),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", action="store_true", help="Send a live request to each model; consumes API quota.")
    parser.add_argument("--model", action="append", dest="models", help="Probe only this model name; repeatable.")
    args = parser.parse_args()

    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    load_dotenv(os.path.join(backend_dir, ".env"), override=False)
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY is not configured in backend/.env")
        return 2

    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        models = list(_catalog_models(client))
    except Exception as error:
        print(f"ERROR: could not read the Gemini model catalog: {_short_error(error)}")
        return 1

    selected_names = set(args.models or [])
    if selected_names:
        models = [model for model in models if getattr(model, "name", "") in selected_names or getattr(model, "name", "").removeprefix("models/") in selected_names]

    print(f"Configured primary: {os.getenv('GEMINI_MODEL', 'not set')}")
    print(f"Configured fallback: {os.getenv('GEMINI_FALLBACK_MODEL', 'not set')}")
    print(f"Text generation models found: {len(models)}")
    print()

    for model in models:
        model_name = str(getattr(model, "name", ""))
        if not args.probe:
            print(f"CATALOG       {model_name}")
            continue
        status, detail = _probe(client, model_name)
        print(f"{status.upper():<18} {model_name}  {detail}")

    return 0


if __name__ == "__main__":
    sys.exit(main())