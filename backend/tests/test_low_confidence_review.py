from unittest.mock import Mock, patch

from src.domain.admin_entities import ReportStatus, ReportType
from src.use_cases.ai.low_confidence_review import check_confidence_and_report


@patch("src.use_cases.ai.low_confidence_review.get_admin_repository")
def test_low_confidence_result_creates_pending_report_for_anonymous_user(
    get_admin_repository,
):
    repository = Mock()
    repository.create_report.side_effect = lambda report: report
    get_admin_repository.return_value = repository

    result = check_confidence_and_report(
        bert_result={
            "is_scam": True,
            "scam_type": "Banking Access & Payment",
            "scam_score": 55.0,
            "legit_score": 45.0,
            "type_confidence": 80.0,
        },
        analysis_ref_id="analysis-123",
        message_preview="Suspicious message preview",
    )

    get_admin_repository.assert_called_once()
    repository.create_report.assert_called_once()
    report = repository.create_report.call_args.args[0]
    assert result.needs_review is True
    assert result.report_id == report.report_id
    assert report.report_type == ReportType.OTHER
    assert report.title == "Automated low-confidence review"
    assert report.status == ReportStatus.PENDING
    assert report.user_id == ""
    assert report.analysis_id == "analysis-123"
    assert report.analysis_ref_id == "analysis-123"
    assert "[AUTO-GENERATED]" in report.description
    assert "Message Preview: N/A" in report.description
    assert "Suspicious message preview" not in report.description
