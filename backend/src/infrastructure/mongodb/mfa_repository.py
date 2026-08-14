"""
MFA Code Repository

Manages storage and validation of multi-factor authentication codes
in MongoDB with automatic TTL-based expiration.

Collections used:
    mfa_codes — stores pending MFA codes with TTL index on `expires_at`

Usage:
    from src.infrastructure.mongodb.mfa_repository import MFACodeRepository

    repo = MFACodeRepository(client, db_name)
    repo.create_mfa_code(user_id, code, expires_at, ip_address)
    is_valid, error = repo.verify_mfa_code(user_id, submitted_code)
"""

import logging
from typing import Optional, Tuple, Dict, Any
from datetime import datetime
from pymongo import MongoClient, ASCENDING
from pymongo.collection import Collection

logger = logging.getLogger(__name__)


class MFACodeRepository:
    """Repository for MFA verification codes backed by MongoDB."""

    def __init__(self, client: MongoClient, database_name: str):
        self.db = client[database_name]
        self.mfa_codes: Collection = self.db.mfa_codes
        self._ensure_indexes()

    # ------------------------------------------------------------------
    # Index management
    # ------------------------------------------------------------------

    def _ensure_indexes(self):
        """Create required indexes (idempotent)."""
        try:
            existing = {idx['name'] for idx in self.mfa_codes.list_indexes()}

            # TTL index for auto-cleanup of expired codes
            if 'expires_at_ttl' not in existing:
                # Drop plain index on expires_at if it exists (prevents conflict)
                if 'expires_at_1' in existing:
                    self.mfa_codes.drop_index('expires_at_1')
                self.mfa_codes.create_index(
                    'expires_at',
                    expireAfterSeconds=0,
                    name='expires_at_ttl',
                )

            # Fast lookup by user_id
            if 'user_id_1' not in existing:
                self.mfa_codes.create_index('user_id', name='user_id_1')

        except Exception as exc:
            logger.warning(f"MFA index setup warning (non-fatal): {exc}")

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    def create_mfa_code(
        self,
        user_id: str,
        code: str,
        expires_at: datetime,
        ip_address: Optional[str] = None,
    ) -> bool:
        """
        Store a new MFA code for *user_id*, replacing any previous one.

        Args:
            user_id: The user this code belongs to.
            code: 6-digit code string.
            expires_at: When this code expires.
            ip_address: IP that requested the code (for auditing).

        Returns:
            True on success, False on error.
        """
        try:
            # Invalidate any previous codes for this user
            self.mfa_codes.delete_many({"user_id": user_id})

            self.mfa_codes.insert_one({
                "user_id": user_id,
                "code": code,
                "created_at": datetime.utcnow(),
                "expires_at": expires_at,
                "ip_address": ip_address,
                "is_used": False,
                "attempts": 0,
            })
            return True
        except Exception as exc:
            logger.error(f"Failed to store MFA code for {user_id}: {exc}")
            return False

    # ------------------------------------------------------------------
    # Verification
    # ------------------------------------------------------------------

    def verify_mfa_code(
        self,
        user_id: str,
        code: str,
        max_attempts: int = 3,
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate a submitted MFA code.

        Checks:
          1. An unexpired, unused code exists for *user_id*.
          2. The attempt count has not exceeded *max_attempts*.
          3. The submitted *code* matches the stored code.

        On success the code is marked as used.
        On failure the attempt counter is incremented.

        Returns:
            (True, None)           — valid
            (False, error_message) — invalid, with human-readable reason
        """
        try:
            record = self.mfa_codes.find_one({
                "user_id": user_id,
                "is_used": False,
                "expires_at": {"$gt": datetime.utcnow()},
            })

            if record is None:
                return False, "No valid MFA code found. Please request a new code."

            if record["attempts"] >= max_attempts:
                # Invalidate the code after too many wrong attempts
                self.mfa_codes.update_one(
                    {"_id": record["_id"]},
                    {"$set": {"is_used": True}},
                )
                return False, "Too many failed attempts. Please request a new code."

            if record["code"] != code:
                self.mfa_codes.update_one(
                    {"_id": record["_id"]},
                    {"$inc": {"attempts": 1}},
                )
                remaining = max_attempts - record["attempts"] - 1
                return False, f"Invalid code. {remaining} attempt(s) remaining."

            # Success — mark as used
            self.mfa_codes.update_one(
                {"_id": record["_id"]},
                {"$set": {"is_used": True}},
            )
            return True, None

        except Exception as exc:
            logger.error(f"MFA verification error for {user_id}: {exc}")
            return False, "Verification error. Please try again."

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_active_code(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Return the currently active (unexpired, unused) code record, or None."""
        return self.mfa_codes.find_one({
            "user_id": user_id,
            "is_used": False,
            "expires_at": {"$gt": datetime.utcnow()},
        })

    def invalidate_codes(self, user_id: str) -> int:
        """Mark all outstanding codes for *user_id* as used. Returns count."""
        result = self.mfa_codes.update_many(
            {"user_id": user_id, "is_used": False},
            {"$set": {"is_used": True}},
        )
        return result.modified_count
