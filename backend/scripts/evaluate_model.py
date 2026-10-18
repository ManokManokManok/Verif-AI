"""
Evaluate the ONNX scam classifier and write backend/models/model_metadata.json.

The metadata holds accuracy, test-set size and a Wilson 95% confidence interval.
The app serves it at GET /api/model-info/ and the UI shows it as the margin of error.

Usage (from backend/):
    python scripts/evaluate_model.py \
        --model "../REFERENCE (dont galaw muna -kench)/Verif-AI-Mk5.onnx" \
        --tokenizer "../REFERENCE (dont galaw muna -kench)/tokenizer.json" \
        --dataset "../REFERENCE (dont galaw muna -kench)/Verif-AI_Dataset_Formatted.xlsx"

Caveat: if the dataset was also used for training, the split is not truly held-out
and the accuracy is optimistic. Pass --dataset pointing at a never-trained-on file
(same sheet layout) to get an honest figure.
"""
import argparse
import json
import math
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

Z_95 = 1.959964


def wilson_interval(correct: int, n: int, z: float = Z_95):
    """Wilson score interval for a binomial proportion (better than Wald near 100%)."""
    p = correct / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return center - half, center + half


def load_samples(path: Path):
    """Read the sheet where each column is '<category> scam' or '<category> legit'."""
    import pandas as pd

    frame = pd.read_excel(path, sheet_name=0)
    samples, seen = [], set()
    for column in frame.columns:
        label = 1 if str(column).strip().lower().endswith('scam') else 0
        for value in frame[column].dropna():
            text = str(value).strip()
            if text and text not in seen:
                seen.add(text)
                samples.append((text, label))
    return samples


def stratified_split(samples, test_fraction: float, seed: int):
    rng = random.Random(seed)
    test = []
    for label in (0, 1):
        group = [s for s in samples if s[1] == label]
        rng.shuffle(group)
        test.extend(group[: round(len(group) * test_fraction)])
    return test


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--model', required=True, type=Path)
    parser.add_argument('--tokenizer', required=True, type=Path)
    parser.add_argument('--dataset', required=True, type=Path)
    parser.add_argument('--test-fraction', type=float, default=0.2,
                        help='Fraction sampled for evaluation; use 1.0 for a pre-made held-out file')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--output', type=Path, default=BACKEND_DIR / 'models' / 'model_metadata.json')
    args = parser.parse_args()

    from src.infrastructure.ai.onnx_model import OnnxMultiHead

    model = OnnxMultiHead(args.model, args.tokenizer)
    samples = load_samples(args.dataset)
    test = samples if args.test_fraction >= 1 else stratified_split(samples, args.test_fraction, args.seed)
    print(f'{len(samples)} unique samples loaded, evaluating {len(test)}')

    correct = 0
    for index, (text, label) in enumerate(test, 1):
        scam_logits, _ = model.predict(text)
        correct += int(int(scam_logits[0].argmax()) == label)
        if index % 100 == 0:
            print(f'  {index}/{len(test)}  running accuracy {correct / index:.4f}')

    n = len(test)
    accuracy = correct / n
    low, high = wilson_interval(correct, n)
    metadata = {
        'accuracy': round(accuracy * 100, 2),
        'correct': correct,
        'n': n,
        'confidence_level': 0.95,
        'ci_low': round(low * 100, 2),
        'ci_high': round(high * 100, 2),
        'margin_of_error': round((high - low) / 2 * 100, 2),
        'method': 'Wilson score interval',
        'split': {'test_fraction': args.test_fraction, 'seed': args.seed, 'dataset_size': len(samples)},
        'evaluated_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    print(json.dumps(metadata, indent=2))


if __name__ == '__main__':
    main()
