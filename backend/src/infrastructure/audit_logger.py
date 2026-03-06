"""
Audit Logging Service

Provides comprehensive audit trail for security-sensitive operations.
Stores audit logs in both file (via Python logging) and MongoDB for
compliance and incident response.

OWASP Reference:
    https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html

Usage:
    from src.infrastructure.audit_logger import get_audit_logger, AuditEventType

    audit = get_audit_logger()
    audit.log_event(
        event_type=AuditEventType.LOGIN_SUCCESS,
        user_id="abc123",
        email="user@example.com",
        ip_address="1.2.3.4",
    )

Note:
    Sensitive data in logs is automatically redacted by the SensitiveDataFilter
    configured in Django settings. Email addresses and other PII are masked
    before being written to log files.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from enum import Enum

from .logging.sensitive_filter import SensitiveDataFilter


class AuditEventType(Enum):
    """Categorised audit event types."""

    # Authentication
    LOGIN_SUCCESS = "auth.login.success"
    LOGIN_FAILED = "auth.login.failed"
    LOGOUT = "auth.logout"
    TOKEN_REFRESH = "auth.token.refresh"
    TOKEN_REFRESH_FAILED = "auth.token.refresh.failed"

    # User management
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    PASSWORD_CHANGED = "user.password.changed"
    PASSWORD_RESET_REQUESTED = "user.password.reset.requested"
    PASSWORD_RESET_COMPLETED = "user.password.reset.completed"
    EMAIL_VERIFICATION_SENT = "user.email.verification.sent"
    EMAIL_VERIFIED = "user.email.verified"

    # Authorisation
    ROLE_ASSIGNED = "authz.role.assigned"
    ROLE_REVOKED = "authz.role.revoked"
    PERMISSION_DENIED = "authz.permission.denied"

    # Data access
    SENSITIVE_DATA_ACCESS = "data.sensitive.access"
    BULK_DATA_EXPORT = "data.bulk.export"

    # Security
    RATE_LIMIT_EXCEEDED = "security.rate_limit.exceeded"
    SUSPICIOUS_ACTIVITY = "security.suspicious.activity"
    VALIDATION_FAILED = "security.validation.failed"

    # MFA
    MFA_CODE_SENT = "auth.mfa.code_sent"
    MFA_CODE_VERIFIED = "auth.mfa.code_verified"
    MFA_CODE_FAILED = "auth.mfa.code_failed"
    MFA_ENABLED = "user.mfa.enabled"
    MFA_DISABLED = "user.mfa.disabled"


class AuditLogger:
    """
    Centralised audit logging service.

    Logs security-sensitive events to both the ``security`` Python logger
    (which writes to ``logs/security.log``) **and** to a MongoDB
    ``audit_logs`` collection when a database connection is available.
    """

    def __init__(self, mongo_collection=None):
        """
        Args:
            mongo_collection: A ``pymongo.collection.Collection`` for
                persistent storage.  ``None`` falls back to file-only logging.
        """
        self.logger = logging.getLogger('security')
        self.audit_collection = mongo_collection
        if self.audit_collection is not None:
            self._ensure_indexes()

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _ensure_indexes(self):
        """Create indexes for efficient audit log querying."""
        try:
            self.audit_collection.create_index("event_type")
            self.audit_collection.create_index("user_id")
            self.audit_collection.create_index("ip_address")
            # TTL index on timestamp: auto-delete audit logs older than 90 days.
            # We use a named index so the TTL param is included.  If the plain
            # "timestamp_1" index already exists, drop it first so the TTL
            # version can be created.
            existing = self.audit_collection.index_information()
            if "timestamp_1" in existing and "expireAfterSeconds" not in existing["timestamp_1"]:
                self.audit_collection.drop_index("timestamp_1")
            if "audit_ttl_90d" not in existing:
                self.audit_collection.create_index(
                    "timestamp",
                    expireAfterSeconds=90 * 24 * 60 * 60,
                    name="audit_ttl_90d",
                )
        except Exception as exc:
            # Index creation failure is non-fatal
            self.logger.warning("Failed to create audit log indexes: %s", exc)

    # ------------------------------------------------------------------
    # Core logging
    # ------------------------------------------------------------------

    def log_event(
        self,
        event_type: AuditEventType,
        *,
        user_id: Optional[str] = None,
        email: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        resource: Optional[str] = None,
        action: Optional[str] = None,
        result: str = "success",
        metadata: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
    ) -> bool:
        """
        Record an audit event.

        Always writes to the file-based ``security`` logger.
        Optionally persists to MongoDB when a collection is configured.

        Returns:
            ``True`` if the event was logged without errors.
        """
        timestamp = datetime.utcnow()

        record: Dict[str, Any] = {
            "timestamp": timestamp,
            "event_type": event_type.value,
            "user_id": user_id,
            "email": self._sanitize_email(email) if email else None,
            "ip_address": ip_address,
            "user_agent": user_agent[:500] if user_agent else None,
            "resource": resource,
            "action": action,
            "result": result,
            "metadata": metadata or {},
            "error_message": error_message,
        }

        # --- File log (always) ---
        log_msg = self._format_log_message(record)
        if result == "success":
            self.logger.info(log_msg)
        else:
            self.logger.warning(log_msg)

        # --- MongoDB (if configured) ---
        if self.audit_collection is not None:
            try:
                self.audit_collection.insert_one(record)
            except Exception as exc:
                self.logger.error(
                    "Failed to persist audit log to MongoDB: %s", exc
                )
                return False

        return True

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def get_user_activity(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[dict]:
        """Return recent audit events for a given user."""
        if self.audit_collection is None:
            return []

        query: Dict[str, Any] = {"user_id": user_id}
        if start_date or end_date:
            query["timestamp"] = {}
            if start_date:
                query["timestamp"]["$gte"] = start_date
            if end_date:
                query["timestamp"]["$lte"] = end_date

        return list(
            self.audit_collection
            .find(query)
            .sort("timestamp", -1)
            .limit(limit)
        )

    def get_failed_logins(self, hours: int = 24, limit: int = 100) -> List[dict]:
        """Return failed login attempts in the last *hours* hours."""
        if self.audit_collection is None:
            return []

        since = datetime.utcnow() - timedelta(hours=hours)
        return list(
            self.audit_collection
            .find({
                "event_type": AuditEventType.LOGIN_FAILED.value,
                "timestamp": {"$gte": since},
            })
            .sort("timestamp", -1)
            .limit(limit)
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _sanitize_email(email: str) -> Optional[str]:
        """Remove control characters to prevent log injection."""
        if not email:
            return None
        return email.replace("\n", "").replace("\r", "")[:254]

    @staticmethod
    def _format_log_message(record: Dict[str, Any]) -> str:
        parts = ["[AUDIT]", f"event={record['event_type']}", f"result={record['result']}"]
        if record.get("user_id"):
            parts.append(f"user_id={record['user_id']}")
        if record.get("email"):
            parts.append(f"email={record['email']}")
        if record.get("ip_address"):
            parts.append(f"ip={record['ip_address']}")
        if record.get("action"):
            parts.append(f"action={record['action']}")
        if record.get("resource"):
            parts.append(f"resource={record['resource']}")
        if record.get("error_message"):
            parts.append(f"error={record['error_message']}")
        return " ".join(parts)


# ======================================================================
# Singleton access
# ======================================================================

_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """
    Return the global ``AuditLogger`` singleton.

    On first call, tries to connect to MongoDB for persistent storage.
    Falls back to file-only logging if the database is unavailable.
    """
    global _audit_logger

    if _audit_logger is None:
        collection = None
        try:
            from .mongodb.connection import get_mongo_client, get_database_name

            client = get_mongo_client()
            db_name = get_database_name()
            collection = client[db_name].audit_logs
        except Exception:
            # Fall back to file-only logging – never crash the app
            logging.getLogger('security').warning(
                "[AUDIT] MongoDB unavailable – audit logs will only be written to file"
            )

        _audit_logger = AuditLogger(mongo_collection=collection)

    return _audit_logger
