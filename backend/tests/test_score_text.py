from src.use_cases.ai.score_text import align_percentages


def test_percentage_alignment_preserves_unrelated_numbers():
    text = 'A score of 1.25 out of 100, or 1.25%. It has 1 pickup point and 2 steps.'
    assert align_percentages(text, 1.25, 0.0, 100.0) == (
        'A score of 0 out of 100, or 0%. It has 1 pickup point and 2 steps.'
    )


def test_percentage_alignment_uses_exact_displayed_scores():
    text = 'About 86% risk, and 14% legit, 40% unrelated.'
    assert align_percentages(text, 85.5, 85.5, 14.5) == (
        'About 85.5% risk, and 14.5% legit, 40% unrelated.'
    )
