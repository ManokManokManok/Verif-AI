import json
from types import SimpleNamespace

import numpy as np
import pytest

from src.apps.core.management.commands.warm_models import Command
from src.infrastructure.ai.onnx_model import find_onnx_assets
from src.use_cases.ai.scam_detection import ScamDetectionUseCase


def test_find_assets_any_filename(tmp_path, monkeypatch):
    (tmp_path / 'my-renamed-model.onnx').write_bytes(b'x')
    (tmp_path / 'tokenizer.json').write_text('{}')
    monkeypatch.setenv('ONNX_MODEL_DIR', str(tmp_path))
    monkeypatch.delenv('ONNX_MODEL_FILE', raising=False)
    model_file, tokenizer_file = find_onnx_assets()
    assert model_file.name == 'my-renamed-model.onnx'
    assert tokenizer_file.name == 'tokenizer.json'


def test_find_assets_missing_tokenizer(tmp_path, monkeypatch):
    (tmp_path / 'model.onnx').write_bytes(b'x')
    monkeypatch.setenv('ONNX_MODEL_DIR', str(tmp_path))
    assert find_onnx_assets() is None


def test_find_assets_missing_folder(tmp_path, monkeypatch):
    monkeypatch.setenv('ONNX_MODEL_DIR', str(tmp_path / 'nope'))
    assert find_onnx_assets() is None


class _FakeOnnx:
    is_onnx = True

    def predict(self, text):
        return np.array([[0.0, 4.0]], dtype=np.float32), np.array([[0.0, 3.0, 0.0]], dtype=np.float32)


def test_onnx_detect_path():
    detector = ScamDetectionUseCase(None, _FakeOnnx(), {0: 'A', 1: 'B', 2: 'C'})
    result = detector.detect('pay a fee now')
    assert result['is_scam'] is True
    assert result['scam_type'] == 'B'
    assert result['scam_score'] > 90
    assert abs(result['scam_score'] + result['legit_score'] - 100) < 0.05


@pytest.mark.parametrize(
    ('model', 'hidden_size'),
    [(_FakeOnnx(), None), (SimpleNamespace(bert=SimpleNamespace(config=SimpleNamespace(hidden_size=768))), 768)],
)
def test_warm_models_accepts_onnx_and_torch_models(monkeypatch, capsys, model, hidden_size):
    monkeypatch.setattr(
        'src.infrastructure.ai.loaders.load_multihead_model',
        lambda: (None, model, {0: 'A'}),
    )

    Command().handle(targets='multihead')

    status = json.loads(capsys.readouterr().out)['multihead']
    assert status['ok'] is True
    assert status['hidden_size'] == hidden_size
