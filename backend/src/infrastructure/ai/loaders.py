from pathlib import Path
import os
import logging
from typing import Optional, Tuple, List

from dotenv import load_dotenv
from huggingface_hub import hf_hub_download

# Avoid noisy logs from llama.cpp if present
logging.getLogger("llama_cpp").setLevel(logging.ERROR)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parents[3]
load_dotenv(BASE_DIR / '.env')

# Defaults can be overridden via environment variables
MULTIHEAD_MODEL_ID = os.getenv('LLM_MULTIHEAD_MODEL_ID', 'ManokManokManok/bimBert_Scam-Detection')
_MULTIHEAD_SUBFOLDER_ENV = os.getenv('LLM_MULTIHEAD_SUBFOLDER', '').strip()
MULTIHEAD_MODEL_SUBFOLDER = None if _MULTIHEAD_SUBFOLDER_ENV.lower() in {'', 'root', '.'} else _MULTIHEAD_SUBFOLDER_ENV
GEMMA_MODEL_ID = os.getenv('LLM_GEMMA_MODEL_ID', 'lmstudio-community/gemma-3-4B-it-qat-GGUF')
GEMMA_GGUF_FILENAME = os.getenv('LLM_GGUF_FILENAME', 'gemma-3-4B-it-QAT-Q4_0.gguf')

# Lazy singletons
_multihead_cache: Optional[Tuple[object, object, dict]] = None
_gemma_cache: Optional[object] = None


def _multihead_subfolder_candidates() -> List[Optional[str]]:
    """Return ordered unique candidate subfolders for model artifacts."""
    candidates: List[Optional[str]] = [MULTIHEAD_MODEL_SUBFOLDER, None, 'mk5', 'mk4']
    deduped: List[Optional[str]] = []
    for candidate in candidates:
        if candidate not in deduped:
            deduped.append(candidate)
    return deduped


def load_multihead_model() -> Tuple[object, object, dict]:
    """Load tokenizer + MultiHeadBERT model + scam_types mapping.
    Heavy imports are done inside to avoid slowing Django startup.
    """
    global _multihead_cache
    if _multihead_cache is not None:
        return _multihead_cache

    # Local imports to keep dependencies optional until used
    from transformers import AutoTokenizer, AutoModel  # type: ignore
    from safetensors.torch import load_file  # type: ignore
    import torch  # type: ignore

    from src.infrastructure.ai.models.multihead_bert import MultiHeadBERT
    from src.domain.scam_types import scam_types

    last_error: Optional[Exception] = None
    for subfolder in _multihead_subfolder_candidates():
        load_kwargs = {'subfolder': subfolder} if subfolder else {}
        try:
            tokenizer = AutoTokenizer.from_pretrained(MULTIHEAD_MODEL_ID, **load_kwargs)
            base_bert = AutoModel.from_pretrained(MULTIHEAD_MODEL_ID, **load_kwargs)
            model = MultiHeadBERT(base_bert, num_scam_types=len(scam_types))

            # Expect weights named 'model.safetensors' in repo root or model subfolder.
            download_kwargs = {'repo_id': MULTIHEAD_MODEL_ID, 'filename': 'model.safetensors'}
            if subfolder:
                download_kwargs['subfolder'] = subfolder
            weights_path = hf_hub_download(**download_kwargs)

            state_dict = load_file(weights_path)
            model.load_state_dict(state_dict)
            model.eval()

            _multihead_cache = (tokenizer, model, scam_types)
            return _multihead_cache
        except Exception as exc:
            last_error = exc
            location = subfolder or 'repo-root'
            logger.warning('Failed loading multihead model from %s: %s', location, exc)

    attempted = [candidate or 'repo-root' for candidate in _multihead_subfolder_candidates()]
    raise RuntimeError(
        f"Unable to load multihead model '{MULTIHEAD_MODEL_ID}'. Tried: {attempted}"
    ) from last_error


def load_gemma_model():
    """Load Gemma GGUF via llama_cpp.Llama, cached.
    """
    global _gemma_cache
    if _gemma_cache is not None:
        return _gemma_cache

    from llama_cpp import Llama  # type: ignore

    model_path = hf_hub_download(repo_id=GEMMA_MODEL_ID, filename=GEMMA_GGUF_FILENAME)
    llm = Llama(model_path=model_path, n_ctx=4096, chat_format='chatml')
    _gemma_cache = llm
    return _gemma_cache


def models_status() -> dict:
    """Return a simple status of whether models are loaded in-memory."""
    return {
        'multihead_loaded': _multihead_cache is not None,
        'gemma_loaded': _gemma_cache is not None,
    }
