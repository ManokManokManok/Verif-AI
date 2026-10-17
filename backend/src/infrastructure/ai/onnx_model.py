"""ONNX runtime wrapper for the multi-head BERT classifier (no torch required)."""
import logging
import os
from pathlib import Path
from typing import Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parents[3]
MAX_LENGTH = 512


def find_onnx_assets() -> Optional[Tuple[Path, Path]]:
    """Return (model_file, tokenizer_json) if an ONNX model folder is present.

    The folder is ONNX_MODEL_DIR or backend/models/onnx. The model may have any
    file name ending in .onnx (override with ONNX_MODEL_FILE).
    """
    folder = Path(os.getenv('ONNX_MODEL_DIR') or (BASE_DIR / 'models' / 'onnx'))
    if not folder.is_dir():
        return None

    wanted = os.getenv('ONNX_MODEL_FILE')
    if wanted:
        model_file = folder / wanted
        candidates = [model_file] if model_file.is_file() else []
    else:
        candidates = sorted(folder.glob('*.onnx'))

    tokenizer_file = folder / 'tokenizer.json'
    if not candidates or not tokenizer_file.is_file():
        return None
    return candidates[0], tokenizer_file


class OnnxMultiHead:
    """Runs the exported model; predict() returns (scam_logits, type_logits) as numpy arrays."""

    is_onnx = True

    def __init__(self, model_path: Path, tokenizer_path: Path):
        import onnxruntime as ort
        from tokenizers import Tokenizer

        self.tokenizer = Tokenizer.from_file(str(tokenizer_path))
        self.tokenizer.enable_truncation(max_length=MAX_LENGTH)

        options = ort.SessionOptions()
        options.enable_cpu_mem_arena = False
        options.enable_mem_pattern = False
        options.intra_op_num_threads = int(os.getenv('ONNX_THREADS', '2'))
        self.session = ort.InferenceSession(
            str(model_path), sess_options=options, providers=['CPUExecutionProvider']
        )
        self._input_names = {item.name for item in self.session.get_inputs()}
        logger.info('[ONNX] Loaded %s', model_path.name)

    def predict(self, text: str) -> Tuple[np.ndarray, np.ndarray]:
        encoding = self.tokenizer.encode(text)
        feeds = {
            'input_ids': np.array([encoding.ids], dtype=np.int64),
            'attention_mask': np.array([encoding.attention_mask], dtype=np.int64),
        }
        feeds = {name: value for name, value in feeds.items() if name in self._input_names}
        scam_logits, type_logits = self.session.run(['scam_logits', 'type_logits'], feeds)
        return scam_logits, type_logits
