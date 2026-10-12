import os
from types import SimpleNamespace

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "verfai.settings")
django.setup()

from src.interfaces.rest.views import (
    _public_analysis_result_fields,
    _public_reviewed_result,
    _user_analysis_title,
)


def test_public_reviewed_result_returns_admin_authored_assessment_without_identity():
    analysis = SimpleNamespace(
        reviewed_result={
            "is_published": True,
            "is_scam": True,
            "risk_score": 84,
            "risk_level": "high",
            "scam_type": "Banking Access & Payment",
            "summary": "This message attempts to steal bank credentials.",
            "details": "The link opens a credential collection page.",
            "key_markers": ["Requests credentials through an unverified link"],
            "explanation": "The sender impersonates a bank.",
            "reviewed_at": "2026-10-12T04:00:00Z",
            "reviewed_by": "admin-123",
        },
        summary="Original model summary.",
    )

    result = _public_reviewed_result(analysis)

    assert result == {
        "is_published": True,
        "is_scam": True,
        "risk_score": 84,
        "risk_level": "high",
        "scam_type": "Banking Access & Payment",
        "summary": "This message attempts to steal bank credentials.",
        "details": "The link opens a credential collection page.",
        "key_markers": ["Requests credentials through an unverified link"],
        "explanation": "The sender impersonates a bank.",
        "reviewed_at": "2026-10-12T04:00:00Z",
    }
    assert "reviewed_by" not in result
    assert _user_analysis_title(analysis, result) == "Admin-reviewed: Banking Access & Payment"
    result_fields = _public_analysis_result_fields(analysis, result)
    assert result_fields["is_scam"] is True
    assert result_fields["scam_score"] is None
    assert result_fields["scam_type"] == "Banking Access & Payment"
    assert result_fields["summary"] == result["summary"]
    assert result_fields["key_markers"] == result["key_markers"]
    assert result_fields["risk_score"] == 84
    assert result_fields["needs_review"] is False


def test_unpublished_admin_review_is_not_exposed_as_the_user_result():
    analysis = SimpleNamespace(
        reviewed_result={"is_published": False, "reviewed_by": "admin-123"},
        summary="Original model summary.",
        scam_type="Banking Access & Payment",
        is_scam=True,
        scam_score=72.0,
        legit_score=28.0,
        label="Scam",
        type_confidence=67.1,
        details="Original model details.",
        key_markers=["Original model flag"],
        needs_review=False,
        review_reason=None,
    )

    assert _public_reviewed_result(analysis) is None
    assert _user_analysis_title(analysis, None) == "Banking Access & Payment"
    assert _public_analysis_result_fields(analysis, None)["summary"] == "Original model summary."
