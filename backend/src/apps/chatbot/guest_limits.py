import logging
import os
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from threading import Lock

logger = logging.getLogger(__name__)

_guest_uses: set[tuple[str, str]] = set()
_guest_uses_lock = Lock()

_COLLECTION = 'guest_uses'
_TTL_DAYS = 30
_index_ready = False


def _use_mongo() -> bool:
    return os.getenv('RATE_LIMIT_BACKEND', 'memory').lower() == 'mongo'


def _collection():
    """Mongo collection with a TTL index so stale guest markers expire on their own."""
    global _index_ready
    from src.infrastructure.mongodb.connection import get_mongo_client, get_database_name
    collection = get_mongo_client()[get_database_name()][_COLLECTION]
    if not _index_ready:
        collection.create_index('expires_at', expireAfterSeconds=0)
        _index_ready = True
    return collection


def _key(session_id: str, feature: str) -> str:
    return f"{sha256(session_id.encode('utf-8')).hexdigest()}:{feature}"


def claim_guest_use(session_id: str, feature: str) -> bool:
    """Allow one use of a feature per anonymous browser session."""
    if _use_mongo():
        try:
            from pymongo.errors import DuplicateKeyError
            try:
                _collection().insert_one({
                    '_id': _key(session_id, feature),
                    'expires_at': datetime.now(timezone.utc) + timedelta(days=_TTL_DAYS),
                })
                return True
            except DuplicateKeyError:
                return False
        except Exception as exc:
            # Fail open so a Mongo outage does not lock guests out.
            logger.error("Guest limit Mongo error: %s", exc)
            return True

    session_hash = sha256(session_id.encode('utf-8')).hexdigest()
    key = (session_hash, feature)

    with _guest_uses_lock:
        if key in _guest_uses:
            return False
        _guest_uses.add(key)
        return True


def release_guest_use(session_id: str, feature: str) -> None:
    """Give back a claimed use (e.g. when the submission was rejected, not analyzed)."""
    if _use_mongo():
        try:
            _collection().delete_one({'_id': _key(session_id, feature)})
        except Exception as exc:
            logger.error("Guest limit Mongo release error: %s", exc)
        return

    key = (sha256(session_id.encode('utf-8')).hexdigest(), feature)
    with _guest_uses_lock:
        _guest_uses.discard(key)
