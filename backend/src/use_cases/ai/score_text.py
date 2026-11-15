"""Helpers for keeping displayed scores and accompanying text consistent."""
import re


LOW_RISK_FLOOR = 20.0

_SCORE_WORDS = re.compile(r"(score[ds]?|scoring|risk|rated|rating|probability|likelihood|chance|confidence)\W{0,12}(of|at|is|was|:)?\W*$", re.I)
_NUMBER = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)(\s?%|\s?/\s?100|\s+out of 100|\s+points?)?(?![\w.]*\d)")


def align_percentages(text: str, raw_scam: float, scam_score: float, legit_score: float) -> str:
    """Align score references in prose with the displayed percentages."""
    def fix(match):
        value = float(match.group(1))
        suffix = match.group(2) or ""
        context = bool(_SCORE_WORDS.search(text[:match.start()][-30:]))
        if suffix:
            tolerance = 1.0
        elif context or "." in match.group(1):
            tolerance = 0.05 if "." in match.group(1) else 0.5
        else:
            return match.group(0)
        if abs(value - raw_scam) < tolerance:
            return f"{scam_score:.2f}".rstrip("0").rstrip(".") + suffix
        if abs(value - (100.0 - raw_scam)) < tolerance:
            return f"{legit_score:.2f}".rstrip("0").rstrip(".") + suffix
        return match.group(0)
    return _NUMBER.sub(fix, text)
