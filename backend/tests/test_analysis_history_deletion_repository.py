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
