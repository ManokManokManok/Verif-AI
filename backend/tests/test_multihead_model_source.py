
import os
import sys
import json
import pytest

# Ensure src/ is on sys.path for direct execution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.infrastructure.ai import loaders
from huggingface_hub import hf_hub_download

def test_multihead_model_source():
    # Load the model using the loader
    tokenizer, model, scam_types = loaders.load_multihead_model()

    # Check model class
    assert model.__class__.__name__.lower().startswith("multihead"), f"Unexpected model class: {model.__class__}"

    # Check that weights are loaded from root (no subfolder)
    model_id = os.getenv('LLM_MULTIHEAD_MODEL_ID', 'ManokManokManok/bimBert_Scam-Detection')
    weights_path = hf_hub_download(repo_id=model_id, filename='model.safetensors')
    assert os.path.exists(weights_path), f"Weights not found at {weights_path}"

    # Optionally, check config.json for a marker (e.g., mk5 version)
    config_path = hf_hub_download(repo_id=model_id, filename='config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    # If you have a version marker, check it here (customize as needed)
    version = config.get('version', '').lower()
    print(f"Loaded model version: {version}")
    print(f"Loaded weights path: {weights_path}")
    # If you want to assert mk5, uncomment below:
    # assert 'mk5' in version or 'mk5' in weights_path, "mk5 not detected in model version or path"

    print("Multihead model loaded successfully from root.")


if __name__ == "__main__":
    print("Running direct model source test...")
    test_multihead_model_source()
