"""
Low Confidence Review Service

Computes whether an AI analysis result needs human review based on confidence thresholds.
Automatically submits reports to admin when low confidence detected.
"""
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import uuid

from ...domain.admin_entities import ReportType, ReportStatus, UserReport
from ...use_cases.admin.user_stats import SubmitUserReportUseCase
from ...infrastructure.mongodb.admin_repository import AdminRepository
from ...infrastructure.mongodb.connection import get_mongo_client, get_database_name


logger = logging.getLogger(__name__)


# Confidence thresholds for triggering review
# NOTE: Set to 99 for testing (will trigger admin review) - REVERT TO 70 AFTER TESTING!
LOW_CONFIDENCE_THRESHOLD = 70.0  # Below this triggers review
HIGH_UNCERTAINTY_THRESHOLD = 40.0  # Margin between scam/legit scores below this is "very uncertain"


@dataclass
class ReviewResult:
    """Result of checking if an analysis needs review."""
    needs_review: bool
    review_reason: Optional[str] = None
    report_id: Optional[str] = None


def get_admin_repository() -> AdminRepository:
    """Get admin repository instance."""
    client = get_mongo_client()
    db_name = get_database_name()
    return AdminRepository(client, db_name)


def check_confidence(
    bert_result: Dict[str, Any],
) -> ReviewResult:
    """
    Check if an analysis result has low confidence and needs human review.
    
    Args:
        bert_result: The BERT detection result containing scam_score, legit_score, etc.
        
    Returns:
        ReviewResult with needs_review flag and reason
    """
    scam_score = bert_result.get('scam_score', 0)
    legit_score = bert_result.get('legit_score', 0)
    is_scam = bert_result.get('is_scam', False)
    type_confidence = bert_result.get('type_confidence', 0)
    
    # Calculate the margin between scores
    margin = abs(scam_score - legit_score)
    
    # Determine the confidence level we're using
    primary_confidence = scam_score if is_scam else legit_score
    
    # Check if review is needed
    needs_review = False
    review_reason = None
    
    # Case 1: Primary confidence is below threshold
    if primary_confidence < LOW_CONFIDENCE_THRESHOLD:
        needs_review = True
        review_reason = f"Low confidence ({primary_confidence:.1f}%)"
    
    # Case 2: Very close scores (high uncertainty)
    elif margin < HIGH_UNCERTAINTY_THRESHOLD:
        needs_review = True
        review_reason = f"High uncertainty (margin: {margin:.1f}%)"
    
    # Case 3: It says "scam" but type_confidence is low
    elif is_scam and type_confidence and type_confidence < 60:
        needs_review = True
        review_reason = f"Low classification confidence ({type_confidence:.1f}%)"
    
    if needs_review:
        logger.info(f"[LOW_CONFIDENCE] Review needed: {review_reason}")
    
    return ReviewResult(needs_review=needs_review, review_reason=review_reason)


def submit_low_confidence_report(
    bert_result: Dict[str, Any],
    analysis_ref_id: str,
    review_reason: str,
    user_id: Optional[str] = None,
    message_preview: Optional[str] = None
) -> Optional[str]:
    """
    Submit an auto-generated report for low-confidence analysis.
    
    Returns:
        Report ID if submitted successfully, None otherwise
    """
    try:
        admin_repo = get_admin_repository()
        submit_usecase = SubmitUserReportUseCase(admin_repo)
        
        # Build description for admin
        scam_score = bert_result.get('scam_score', 0)
        legit_score = bert_result.get('legit_score', 0)
        is_scam = bert_result.get('is_scam', False)
        scam_type = bert_result.get('scam_type', 'Unknown')
        
        description = f"""[AUTO-GENERATED] Low Confidence Detection Report

Reason: {review_reason}

Analysis Details:
- Result: {"SCAM" if is_scam else "NOT SCAM"}
- Scam Type: {scam_type}
- Scam Score: {scam_score:.1f}%
- Legit Score: {legit_score:.1f}%
- Ref ID: {analysis_ref_id}

Message Preview: {message_preview[:200] if message_preview else 'N/A'}...

This report was automatically generated because the AI model's confidence was below the threshold for reliable detection. Please review this analysis manually."""

        report = submit_usecase.submit_report(
            report_type=ReportType.LOW_CONFIDENCE,
            description=description,
            analysis_id=analysis_ref_id,
            user_id=user_id,
            user_email=None
        )
        
        logger.info(f"[LOW_CONFIDENCE] Auto-submitted report: {report.id}")
        return report.id
        
    except Exception as e:
        logger.error(f"[LOW_CONFIDENCE] Failed to submit report: {e}")
        return None


def check_confidence_and_report(
    bert_result: Dict[str, Any],
    analysis_ref_id: str = None,
    user_id: Optional[str] = None,
    message_preview: Optional[str] = None
) -> ReviewResult:
    """
    Check confidence and auto-submit report to admin if review is needed.
    """
    result = check_confidence(bert_result)
    
    if result.needs_review and analysis_ref_id:
        report_id = submit_low_confidence_report(
            bert_result=bert_result,
            analysis_ref_id=analysis_ref_id,
            review_reason=result.review_reason,
            user_id=user_id,
            message_preview=message_preview
        )
        result.report_id = report_id
    
    return result
    return check_confidence(bert_result)