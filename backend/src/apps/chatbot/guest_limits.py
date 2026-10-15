from hashlib import sha256
from threading import Lock


_guest_uses: set[tuple[str, str]] = set()
_guest_uses_lock = Lock()


def claim_guest_use(session_id: str, feature: str) -> bool:
    """Allow one use of a feature per anonymous browser session."""
    session_hash = sha256(session_id.encode('utf-8')).hexdigest()
    key = (session_hash, feature)

    with _guest_uses_lock:
        if key in _guest_uses:
            return False
        _guest_uses.add(key)
        return True


def release_guest_use(session_id: str, feature: str) -> None:
    """Give back a claimed use (e.g. when the submission was rejected, not analyzed)."""
    key = (sha256(session_id.encode('utf-8')).hexdigest(), feature)
    with _guest_uses_lock:
        _guest_uses.discard(key)
