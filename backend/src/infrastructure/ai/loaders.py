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


# Only model ID is needed; always load from root
MULTIHEAD_MODEL_ID = os.getenv('LLM_MULTIHEAD_MODEL_ID', 'ManokManokManok/bimBert_Scam-Detection')
GEMMA_MODEL_ID = os.getenv('LLM_GEMMA_MODEL_ID', 'lmstudio-community/gemma-3-4B-it-qat-GGUF')
GEMMA_GGUF_FILENAME = os.getenv('LLM_GGUF_FILENAME', 'gemma-3-4B-it-QAT-Q4_0.gguf')

# Lazy singletons
_multihead_cache: Optional[Tuple[object, object, dict]] = None
_gemma_cache: Optional[object] = None





def load_multihead_model() -> Tuple[object, object, dict]:
    """Load tokenizer + MultiHeadBERT model + scam_types mapping from repo root only."""
    global _multihead_cache
    if _multihead_cache is not None:
        return _multihead_cache

    # Local imports to keep dependencies optional until used
    from transformers import AutoTokenizer, AutoModel  # type: ignore
    from safetensors.torch import load_file  # type: ignore
    import torch  # type: ignore

    from src.infrastructure.ai.models.multihead_bert import MultiHeadBERT
    from src.domain.scam_types import scam_types

    try:
        tokenizer = AutoTokenizer.from_pretrained(MULTIHEAD_MODEL_ID)
        base_bert = AutoModel.from_pretrained(MULTIHEAD_MODEL_ID)
        model = MultiHeadBERT(base_bert, num_scam_types=len(scam_types))

        # Expect weights named 'model.safetensors' in repo root only.
        weights_path = hf_hub_download(repo_id=MULTIHEAD_MODEL_ID, filename='model.safetensors')

        state_dict = load_file(weights_path)
        model.load_state_dict(state_dict)
        model.eval()

        _multihead_cache = (tokenizer, model, scam_types)
        return _multihead_cache
    except Exception as exc:
        logger.error('Failed loading multihead model from repo root: %s', exc)
        raise RuntimeError(
            f"Unable to load multihead model '{MULTIHEAD_MODEL_ID}' from repo root."
        ) from exc


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
