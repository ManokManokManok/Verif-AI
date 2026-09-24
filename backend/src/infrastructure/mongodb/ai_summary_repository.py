"""
AI Analytics Summary Repository

MongoDB repository for storing plain-language, AI-generated analytics
summaries per user. Enforces persistence of when a summary was made so
callers can implement a cooldown and avoid excessive Gemini calls.

Collection Schema:
{
    "_id": ObjectId,
    "user_id": str,
    "input_hash": str,       # hash of the compact stats snapshot used to build this summary
    "headline": str,
    "risk_tag": str,         # "low" | "medium" | "high"
    "body": List[str],
    "tip": str,
    "source": str,           # "gemini" | "fallback"
    "created_at": datetime,
    "expires_at": datetime,  # TTL - document auto-removed after this time
}
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from ...domain.ai_summary_entities import AIAnalyticsSummary


class AIAnalyticsSummaryRepository:
    """MongoDB repository for AI-generated analytics summaries."""

    COLLECTION_NAME = "ai_analytics_summaries"

    def __init__(self, client: MongoClient, database_name: str):
        self.db: Database = client[database_name]
        self.collection: Collection = self.db[self.COLLECTION_NAME]
        self._ensure_indexes()

    def _ensure_indexes(self) -> None:
        """Create indexes for efficient queries (idempotent)."""
        existing = {idx['name'] for idx in self.collection.list_indexes()}

        if 'expires_at_ttl' not in existing:
            if 'expires_at_1' in existing:
                self.collection.drop_index('expires_at_1')
            self.collection.create_index('expires_at', expireAfterSeconds=0, name='expires_at_ttl')

        if 'user_id_created_at' not in existing:
            self.collection.create_index(
                [("user_id", 1), ("created_at", -1)], name='user_id_created_at'
            )

    def get_latest(self, user_id: str) -> Optional[AIAnalyticsSummary]:
        """Fetch the most recently generated summary for a user, if any."""
        doc = self.collection.find_one(
            {"user_id": str(user_id)},
            sort=[("created_at", -1)],
        )
        if not doc:
            return None
        return self._document_to_entity(doc)

    def save(self, summary: AIAnalyticsSummary) -> AIAnalyticsSummary:
        """Insert a new summary document for a user."""
        summary.created_at = summary.created_at or datetime.utcnow()
        self.collection.insert_one(self._entity_to_document(summary))
        return summary

    def touch_expiry(self, user_id: str, input_hash: str, expires_at: datetime) -> bool:
        """Extend the TTL of the latest matching summary without calling the AI again."""
        doc = self.collection.find_one(
            {"user_id": str(user_id), "input_hash": input_hash},
            sort=[("created_at", -1)],
        )
        if not doc:
            return False
        result = self.collection.update_one(
            {"_id": doc["_id"]},
            {"$set": {"expires_at": expires_at}},
        )
        return result.modified_count > 0

    @staticmethod
    def _entity_to_document(summary: AIAnalyticsSummary) -> Dict[str, Any]:
        return {
            "user_id": summary.user_id,
            "input_hash": summary.input_hash,
            "headline": summary.headline,
            "risk_tag": summary.risk_tag,
            "current_status": list(summary.current_status),
            "your_journey": list(summary.your_journey),
            "community_trends": list(summary.community_trends),
            "watch_list": list(summary.watch_list),
            "tip": summary.tip,
            "source": summary.source,
            "created_at": summary.created_at,
            "expires_at": summary.expires_at,
        }

    @staticmethod
    def _document_to_entity(doc: Dict[str, Any]) -> AIAnalyticsSummary:
        return AIAnalyticsSummary(
            user_id=doc.get("user_id"),
            input_hash=doc.get("input_hash", ""),
            headline=doc.get("headline", ""),
            risk_tag=doc.get("risk_tag", "low"),
            current_status=list(doc.get("current_status") or []),
            your_journey=list(doc.get("your_journey") or []),
            community_trends=list(doc.get("community_trends") or []),
            watch_list=list(doc.get("watch_list") or []),
            tip=doc.get("tip", ""),
            source=doc.get("source", "fallback"),
            created_at=doc.get("created_at"),
            expires_at=doc.get("expires_at"),
        )
