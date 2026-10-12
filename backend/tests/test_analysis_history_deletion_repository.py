from unittest.mock import MagicMock

from bson import ObjectId

from src.infrastructure.mongodb.analysis_repository import AnalysisResultRepository


def _make_repo():
    collection = MagicMock()
    db = MagicMock()
    db.__getitem__.return_value = collection
    client = MagicMock()
    client.__getitem__.return_value = db

    repo = AnalysisResultRepository(client, "test_db")
    return repo, collection


def test_get_by_user_id_excludes_soft_deleted_by_default():
    repo, collection = _make_repo()

    cursor = MagicMock()
    cursor.sort.return_value = cursor
    cursor.limit.return_value = []
    collection.find.return_value = cursor

    repo.get_by_user_id("user-123", limit=25)

    collection.find.assert_called_once_with(
        {
            "user_id": "user-123",
            "$or": [
                {"user_deleted": {"$exists": False}},
                {"user_deleted": False},
            ],
        }
    )


def test_get_by_user_id_can_include_soft_deleted():
    repo, collection = _make_repo()

    cursor = MagicMock()
    cursor.sort.return_value = cursor
    cursor.limit.return_value = []
    collection.find.return_value = cursor

    repo.get_by_user_id("user-123", include_deleted=True)

    collection.find.assert_called_once_with({"user_id": "user-123"})


def test_soft_delete_for_user_marks_record_and_redacts_message():
    repo, collection = _make_repo()
    collection.update_one.return_value.modified_count = 1

    analysis_id = "507f1f77bcf86cd799439011"
    deleted = repo.soft_delete_for_user(analysis_id, "user-123")

    assert deleted is True

    call_args = collection.update_one.call_args[0]
    query, update_doc = call_args

    assert query["_id"] == ObjectId(analysis_id)
    assert query["user_id"] == "user-123"
    assert "$or" in query

    set_doc = update_doc["$set"]
    assert set_doc["user_deleted"] is True
    assert set_doc["deleted_by_user_id"] == "user-123"
    assert set_doc["message"] is None
    assert "user_deleted_at" in set_doc


def test_soft_delete_all_for_user_returns_modified_count():
    repo, collection = _make_repo()
    collection.update_many.return_value.modified_count = 3

    deleted_count = repo.soft_delete_all_for_user("user-123")

    assert deleted_count == 3

    query, update_doc = collection.update_many.call_args[0]
    assert query["user_id"] == "user-123"
    assert "$or" in query
    assert update_doc["$set"]["user_deleted"] is True
    assert update_doc["$set"]["message"] is None


def test_update_reviewed_result_preserves_model_output_and_appends_history():
    repo, collection = _make_repo()
    review = {
        "decision": "confirmed_legitimate",
        "is_published": True,
        "is_scam": False,
        "risk_level": "low",
        "scam_type": "Legitimate content",
        "explanation": "Verified as a legitimate message.",
        "reviewed_by": "admin-1",
        "reviewed_at": "2026-10-12T00:00:00",
        "report_id": "report-1",
    }
    collection.find_one.return_value = {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "ref_id": "analysis-1",
        "scam_class": 0,
        "scam_type": "Banking scam",
        "confidence_bps": 8200,
        "is_scam": True,
        "analyzer_type": "bert",
        "analyzer_version": "v1",
        "reviewed_result": review,
        "review_history": [review],
    }

    result = repo.update_reviewed_result("analysis-1", review, review)

    update = collection.update_one.call_args.args[1]
    assert update["$set"] == {"reviewed_result": review}
    assert update["$push"] == {"review_history": review}
    assert result.is_scam is True
    assert result.reviewed_result == review
    assert result.review_history == [review]


def test_set_review_publication_updates_only_review_for_matching_report():
    repo, collection = _make_repo()
    collection.update_one.return_value.matched_count = 1

    assert repo.set_review_publication("analysis-1", "report-1", True) is True

    collection.update_one.assert_called_once_with(
        {
            "ref_id": "analysis-1",
            "reviewed_result.report_id": "report-1",
        },
        {"$set": {"reviewed_result.is_published": True}},
    )
