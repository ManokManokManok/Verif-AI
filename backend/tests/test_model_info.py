from src.infrastructure.model_info import load_accuracy_metadata


def test_accuracy_is_available_without_evaluation_metadata(monkeypatch, tmp_path):
    monkeypatch.delenv('MODEL_REPORTED_ACCURACY', raising=False)
    monkeypatch.setenv('MODEL_METADATA_FILE', str(tmp_path / 'missing.json'))

    assert load_accuracy_metadata() == {'accuracy': 94.7, 'margin_of_error': 4.4}


def test_reported_accuracy_remains_configurable(monkeypatch):
    monkeypatch.setenv('MODEL_REPORTED_ACCURACY', '92.5')

    assert load_accuracy_metadata()['accuracy'] == 92.5
