import sys
from copy import deepcopy
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from pymongo.errors import DuplicateKeyError

backend_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_dir))

from src.domain.entities import User, UserNotFoundError
from src.infrastructure.mongodb.repositories import MongoDBTokenRepository
from src.use_cases.security_auth import InvalidTokenError, PasswordResetUseCase


class _InMemoryCollection:
    def __init__(self):
        self.documents = []
        self.next_id = 1

    def create_index(self, *_args, **_kwargs):
        return None

    def find_one(self, query):
        return deepcopy(next((doc for doc in self.documents if self._matches(doc, query)), None))

    def insert_one(self, document):
        if any(doc.get("email_key") == document.get("email_key") for doc in self.documents):
            raise DuplicateKeyError("duplicate email key")
        inserted = deepcopy(document)
        inserted["_id"] = self.next_id
        self.next_id += 1
        self.documents.append(inserted)
        return type("InsertResult", (), {"inserted_id": inserted["_id"]})()

    def update_one(self, query, update):
        document = next((doc for doc in self.documents if self._matches(doc, query)), None)
        if document is None:
            return type("UpdateResult", (), {"modified_count": 0})()
        for key, value in update.get("$set", {}).items():
            document[key] = deepcopy(value)
        for key, value in update.get("$inc", {}).items():
            document[key] = document.get(key, 0) + value
        return type("UpdateResult", (), {"modified_count": 1})()

    def find_one_and_update(self, query, update, return_document=False):
        matching = next((doc for doc in self.documents if self._matches(doc, query)), None)
        if matching is None:
            return None
        self.update_one(query, update)
        return deepcopy(next(doc for doc in self.documents if doc["_id"] == matching["_id"]))

    @staticmethod
    def _matches(document, query):
        for key, expected in query.items():
            exists = key in document
            actual = document.get(key)
            if isinstance(expected, dict):
                if "$exists" in expected and exists != expected["$exists"]:
                    return False
                if "$gt" in expected and not (actual is not None and actual > expected["$gt"]):
                    return False
                if "$lt" in expected and not (actual is not None and actual < expected["$lt"]):
                    return False
            elif actual != expected:
                return False
        return True


class _InMemoryDatabase:
    def __init__(self):
        self.collections = {}

    def __getattr__(self, name):
        return self.collections.setdefault(name, _InMemoryCollection())


class _InMemoryClient:
    def __init__(self):
        self.database = _InMemoryDatabase()

    def __getitem__(self, _name):
        return self.database


class _UserRepository:
    def __init__(self, user=None):
        self.user = user

    def get_by_email(self, _email):
        if not self.user:
            raise UserNotFoundError()
        return self.user


class _EmailService:
    def __init__(self, sent=True):
        self.sent = sent
        self.codes = []

    def send_password_reset_code_email(self, _email, code):
        self.codes.append(code)
        return self.sent


class _PasswordHasher:
    def hash_password(self, password):
        return f"hashed:{password}"


class _PasswordValidator:
    def validate(self, password):
        valid = password == "StrongPassword1!"
        return valid, [] if valid else ["invalid password"]


class _TokenGenerator:
    pass


def _use_case(user_repo, token_repo, email_service):
    return PasswordResetUseCase(
        user_repository=user_repo,
        token_repository=token_repo,
        email_service=email_service,
        token_generator=_TokenGenerator(),
        password_hasher=_PasswordHasher(),
        password_validator=_PasswordValidator(),
    )


@pytest.fixture(autouse=True)
def _stable_reset_secret(monkeypatch):
    monkeypatch.setenv("PASSWORD_RESET_CODE_SECRET", "stable-test-secret")


def test_unknown_email_gets_same_request_result_without_sending_email():
    token_repo = MongoDBTokenRepository(_InMemoryClient(), "test")
    email_service = _EmailService()
    use_case = _use_case(_UserRepository(), token_repo, email_service)

    result = use_case.request_password_reset_code("unknown@example.com")

    assert result["status"] == "sent"
    assert result["retry_after_seconds"] == 60
    assert email_service.codes == []
    stored = token_repo.password_reset_codes_collection.find_one(
        {"email_key": token_repo.password_reset_codes_collection.documents[0]["email_key"]}
    )
    assert stored["user_id"] is None
    assert len(stored["code_digest"]) == 64


def test_failed_email_delivery_invalidates_the_issued_code():
    token_repo = MongoDBTokenRepository(_InMemoryClient(), "test")
    user = User(id="user-1", email="person@example.com", username="person", password_hash="old", roles=[])
    email_service = _EmailService(sent=False)
    use_case = _use_case(_UserRepository(user), token_repo, email_service)

    result = use_case.request_password_reset_code(user.email)
    stored = token_repo.password_reset_codes_collection.documents[0]

    assert result["status"] == "email_failed"
    assert stored["expires_at"] <= datetime.utcnow()
    assert token_repo.record_password_reset_code_attempt(
        stored["email_key"], stored["code_digest"], datetime.utcnow()
    )["status"] == "invalid"


def test_code_replacement_enforces_cooldown_and_hourly_send_limit():
    token_repo = MongoDBTokenRepository(_InMemoryClient(), "test")
    now = datetime(2026, 1, 1)

    first = token_repo.issue_password_reset_code("email-key", "user-1", "digest-1", now)
    cooldown = token_repo.issue_password_reset_code(
        "email-key", "user-1", "digest-too-soon", now + timedelta(seconds=59)
    )
    second = token_repo.issue_password_reset_code(
        "email-key", "user-1", "digest-2", now + timedelta(seconds=60)
    )
    third = token_repo.issue_password_reset_code(
        "email-key", "user-1", "digest-3", now + timedelta(seconds=120)
    )
    limited = token_repo.issue_password_reset_code(
        "email-key", "user-1", "digest-4", now + timedelta(seconds=180)
    )

    assert first["status"] == "sent"
    assert cooldown["status"] == "cooldown"
    assert second["status"] == third["status"] == "sent"
    assert limited["status"] == "send_limit"
    assert limited["send_limit_reached"] is True
    assert token_repo.record_password_reset_code_attempt(
        "email-key", "digest-1", now + timedelta(seconds=181)
    )["status"] == "wrong"


def test_code_expires_after_ten_minutes_and_is_single_use():
    token_repo = MongoDBTokenRepository(_InMemoryClient(), "test")
    now = datetime(2026, 1, 1)
    token_repo.issue_password_reset_code("email-key", "user-1", "digest", now)

    expired = token_repo.record_password_reset_code_attempt(
        "email-key", "digest", now + timedelta(minutes=10)
    )
    assert expired["status"] == "invalid"

    token_repo.issue_password_reset_code(
        "email-key", "user-1", "new-digest", now + timedelta(minutes=10, seconds=1)
    )
    valid = token_repo.record_password_reset_code_attempt(
        "email-key", "new-digest", now + timedelta(minutes=10, seconds=2)
    )
    replay = token_repo.record_password_reset_code_attempt(
        "email-key", "new-digest", now + timedelta(minutes=10, seconds=3)
    )
    assert valid == {"status": "valid", "user_id": "user-1"}
    assert replay["status"] == "invalid"


def test_five_wrong_attempts_lock_code():
    token_repo = MongoDBTokenRepository(_InMemoryClient(), "test")
    now = datetime(2026, 1, 1)
    token_repo.issue_password_reset_code("email-key", "user-1", "right-digest", now)

    statuses = [
        token_repo.record_password_reset_code_attempt(
            "email-key", "wrong-digest", now + timedelta(seconds=attempt)
        )["status"]
        for attempt in range(1, 6)
    ]
    sixth = token_repo.record_password_reset_code_attempt(
        "email-key", "wrong-digest", now + timedelta(seconds=6)
    )
    assert statuses == ["wrong", "wrong", "wrong", "wrong", "locked"]
    assert sixth["status"] == "locked"


def test_invalid_new_password_does_not_consume_code():
    token_repo = MongoDBTokenRepository(_InMemoryClient(), "test")
    user = User(id="user-1", email="person@example.com", username="person", password_hash="old", roles=[])
    token_repo.issue_password_reset_code(
        "email-key", "user-1", "unused-digest", datetime.utcnow()
    )
    use_case = _use_case(_UserRepository(user), token_repo, _EmailService())

    with pytest.raises(ValueError):
        use_case.reset_password_with_code("person@example.com", "123456", "weak")

    assert token_repo.password_reset_codes_collection.documents[0].get("consumed_at") is None


def test_valid_code_resets_password_and_cannot_be_reused():
    class _TrackingTokenRepository(MongoDBTokenRepository):
        def __init__(self):
            super().__init__(_InMemoryClient(), "test")
            self.saved_password_hash = None

        def update_user_password(self, user_id, password_hash):
            self.saved_password_hash = (user_id, password_hash)
            return True

    token_repo = _TrackingTokenRepository()
    user = User(id="user-1", email="person@example.com", username="person", password_hash="old", roles=[])
    user_repo = _UserRepository(user)
    email_service = _EmailService()
    use_case = _use_case(user_repo, token_repo, email_service)
    use_case.request_password_reset_code(user.email)
    code = email_service.codes[0]

    assert use_case.reset_password_with_code(
        user.email, code, "StrongPassword1!"
    ) == user.id
    assert token_repo.saved_password_hash == (user.id, "hashed:StrongPassword1!")

    with pytest.raises(InvalidTokenError):
        use_case.reset_password_with_code(user.email, code, "StrongPassword1!")
