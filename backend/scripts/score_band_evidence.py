"""
Score a random sample of the labelled dataset with the local BERT classifier and report where
scam vs legit messages land, to justify the risk-band cutoffs.

Usage (from backend/):
  python scripts/score_band_evidence.py --path "../REFERENCE (dont galaw muna -kench)/Verif-AI_Dataset_Formatted.xlsx" --per-label 200

Results are also saved to score_band_evidence.csv.
"""
import argparse
import os
import sys

import pandas as pd
from dotenv import load_dotenv

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)
load_dotenv(os.path.join(BACKEND_DIR, ".env"), override=False)

from src.infrastructure.ai.loaders import load_multihead_model  # noqa: E402
from src.use_cases.ai.scam_detection import ScamDetectionUseCase  # noqa: E402

BINS = [(0, 20), (21, 40), (41, 60), (61, 80), (81, 100)]


def sample_messages(path: str, per_label: int, seed: int) -> list:
    sheet = pd.read_excel(path, sheet_name="Dataset")
    rows = []
    for label, suffix in (("scam", " scam"), ("legit", " legit")):
        pool = []
        for col in sheet.columns:
            if col.endswith(suffix):
                pool += [(label, col, str(m)) for m in sheet[col].dropna()]
        pool = pd.DataFrame(pool, columns=["label", "category", "message"])
        rows.append(pool.sample(n=min(per_label, len(pool)), random_state=seed))
    return pd.concat(rows, ignore_index=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", required=True)
    parser.add_argument("--per-label", type=int, default=40)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    data = sample_messages(args.path, args.per_label, args.seed)
    tokenizer, model, scam_types = load_multihead_model()
    classifier = ScamDetectionUseCase(tokenizer, model, scam_types)

    scores = []
    for i, row in data.iterrows():
        try:
            scores.append(classifier.detect(row["message"])["scam_score"])
        except Exception as error:
            print(f"[{i}] failed: {error}")
            scores.append(None)
    data["score"] = scores
    data = data.dropna(subset=["score"])
    data.to_csv(os.path.join(BACKEND_DIR, "score_band_evidence.csv"), index=False)

    print("\nScore distribution (count of messages per band)")
    print(f"{'band':>9} {'scam':>6} {'legit':>6} {'% actually scam':>16}")
    for lo, hi in BINS:
        in_band = data[(data.score >= lo) & (data.score <= hi)]
        scam = int((in_band.label == "scam").sum())
        legit = int((in_band.label == "legit").sum())
        pct = f"{100 * scam / (scam + legit):.0f}%" if scam + legit else "-"
        print(f"{lo:>4}-{hi:<4} {scam:>6} {legit:>6} {pct:>16}")

    print("\nMedian score:", data.groupby("label").score.median().to_dict())
    return 0


if __name__ == "__main__":
    sys.exit(main())
