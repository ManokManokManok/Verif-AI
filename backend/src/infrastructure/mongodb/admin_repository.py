"""
Admin MongoDB Repository

Repository for admin dashboard data including analysis statistics,
user statistics, user reports, and admin activity logs.
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta, timezone
from pymongo import MongoClient, DESCENDING, ASCENDING
from pymongo.collection import Collection
from pymongo.database import Database
from bson import ObjectId
import logging

from ...domain.admin_entities import (
    AnalysisStatistics,
    UserStatistics,
    UserReport,
    AdminActivityLog,
    ScamCategoryBreakdown,
    ReportStatus,
    ReportType,
    StatisticsPeriod,
    ReportNotFoundError,
)

logger = logging.getLogger(__name__)


class AdminRepository:
    """
    MongoDB repository for admin dashboard data.
    
    Provides aggregation queries for statistics and CRUD operations
    for user reports and admin activity logs.
    """
    
    def __init__(self, client: MongoClient, database_name: str):
        self.db: Database = client[database_name]
        self.analysis_collection: Collection = self.db.analysis_results
        self.users_collection: Collection = self.db.users
        self.reports_collection: Collection = self.db.user_reports
        self.activity_logs_collection: Collection = self.db.admin_activity_logs
        self.visits_collection: Collection = self.db.website_visits
        self._ensure_indexes()
    
    def _ensure_indexes(self) -> None:
        """Create indexes for efficient queries."""
        # Reports indexes
        self.reports_collection.create_index("report_id", unique=True)
        self.reports_collection.create_index("user_id")
        self.reports_collection.create_index("status")
        self.reports_collection.create_index("created_at")
        self.reports_collection.create_index([("status", ASCENDING), ("created_at", DESCENDING)])
        
        # Activity logs indexes
        self.activity_logs_collection.create_index("log_id", unique=True)
        self.activity_logs_collection.create_index("admin_user_id")
        self.activity_logs_collection.create_index("created_at")
        self.activity_logs_collection.create_index("action")
        
        # Visits indexes (if collection exists)
        try:
            self.visits_collection.create_index("timestamp")
            self.visits_collection.create_index("path")
            self.visits_collection.create_index([("timestamp", DESCENDING)])
        except Exception:
            pass
    
    # ==================== Analysis Statistics ====================

    def _resolve_statistics_date_range(
        self,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        period: StatisticsPeriod
    ) -> Tuple[Optional[datetime], Optional[datetime]]:
        """Resolve effective date range from explicit dates or period."""
        if start_date or end_date:
            return start_date, end_date

        if period == StatisticsPeriod.ALL_TIME:
            return None, None

        now = datetime.utcnow()
        if period == StatisticsPeriod.DAY:
            return now - timedelta(days=1), now
        if period == StatisticsPeriod.WEEK:
            return now - timedelta(days=7), now
        if period == StatisticsPeriod.MONTH:
            return now - timedelta(days=30), now
        if period == StatisticsPeriod.YEAR:
            return now - timedelta(days=365), now

        return None, None

    def _build_created_at_filter(
        self,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> Dict[str, Any]:
        """Build created_at date filter for Mongo match stages."""
        date_filter: Dict[str, Any] = {}
        if start_date:
            date_filter["$gte"] = start_date
        if end_date:
            date_filter["$lte"] = end_date
        return date_filter

    def _to_utc_naive(self, value: Optional[datetime]) -> Optional[datetime]:
        """Convert datetime to UTC-naive for Mongo comparisons."""
        if value is None:
            return None
        if value.tzinfo is None:
            return value
        return value.astimezone(timezone.utc).replace(tzinfo=None)

    def _get_summary_counts(
        self,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> Dict[str, int]:
        """Get summary counts for a date range."""
        match_stage: Dict[str, Any] = {}
        date_filter = self._build_created_at_filter(start_date, end_date)
        if date_filter:
            match_stage["created_at"] = date_filter

        pipeline: List[Dict[str, Any]] = []
        if match_stage:
            pipeline.append({"$match": match_stage})

        pipeline.append({
            "$group": {
                "_id": None,
                "total_count": {"$sum": 1},
                "scam_count": {
                    "$sum": {"$cond": [{"$eq": ["$is_scam", True]}, 1, 0]}
                },
                "legitimate_count": {
                    "$sum": {"$cond": [{"$eq": ["$is_scam", False]}, 1, 0]}
                },
                "high_risk_count": {
                    "$sum": {
                        "$cond": [
                            {"$and": [
                                {"$eq": ["$is_scam", True]},
                                {"$or": [
                                    {"$gte": ["$confidence_bps", 7000]},
                                    {"$gte": ["$scam_score", 0.7]}
                                ]}
                            ]},
                            1, 0
                        ]
                    }
                },
                "medium_risk_count": {
                    "$sum": {
                        "$cond": [
                            {"$and": [
                                {"$eq": ["$is_scam", True]},
                                {"$or": [
                                    {"$and": [
                                        {"$gte": ["$confidence_bps", 4000]},
                                        {"$lt": ["$confidence_bps", 7000]}
                                    ]},
                                    {"$and": [
                                        {"$gte": ["$scam_score", 0.4]},
                                        {"$lt": ["$scam_score", 0.7]}
                                    ]}
                                ]}
                            ]},
                            1, 0
                        ]
                    }
                },
            }
        })

        result = list(self.analysis_collection.aggregate(pipeline))
        if not result:
            return {
                "total_count": 0,
                "scam_count": 0,
                "legitimate_count": 0,
                "high_risk_count": 0,
                "medium_risk_count": 0,
            }
        return result[0]

    def _get_previous_period_bounds(
        self,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
    ) -> Tuple[Optional[datetime], Optional[datetime]]:
        """Get previous period date bounds based on current effective bounds."""
        if not start_date or not end_date:
            return None, None

        if end_date <= start_date:
            return None, None

        duration = end_date - start_date
        previous_end = start_date
        previous_start = start_date - duration
        return previous_start, previous_end
    
    def get_analysis_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        period: StatisticsPeriod = StatisticsPeriod.ALL_TIME
    ) -> AnalysisStatistics:
        """
        Get aggregated analysis statistics.
        
        Args:
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)
            period: Time period for grouping
            
        Returns:
            AnalysisStatistics entity with aggregated data
        """
        effective_start_date, effective_end_date = self._resolve_statistics_date_range(
            start_date=start_date,
            end_date=end_date,
            period=period,
        )

        stats = self._get_summary_counts(
            start_date=effective_start_date,
            end_date=effective_end_date,
        )

        total = stats.get("total_count", 0)
        high_risk = stats.get("high_risk_count", 0)
        medium_risk = stats.get("medium_risk_count", 0)
        scam_total = stats.get("scam_count", 0)
        legitimate = stats.get("legitimate_count", 0)
        low_risk = max(0, scam_total - high_risk - medium_risk)

        previous_total = 0
        previous_scam_total = 0
        previous_start, previous_end = self._get_previous_period_bounds(
            start_date=effective_start_date,
            end_date=effective_end_date,
        )
        if previous_start and previous_end:
            previous_stats = self._get_summary_counts(
                start_date=previous_start,
                end_date=previous_end,
            )
            previous_total = previous_stats.get("total_count", 0)
            previous_scam_total = previous_stats.get("scam_count", 0)
        
        # Get category breakdown
        categories = self.get_top_scam_categories(
            start_date=effective_start_date,
            end_date=effective_end_date,
            period=period,
            limit=15,
        )
        
        # Get daily counts for trend
        daily_counts = self._get_daily_analysis_counts(effective_start_date, effective_end_date)
        previous_daily_counts = self._get_daily_analysis_counts(previous_start, previous_end) if previous_start and previous_end else []
        confidence_distribution = self._get_confidence_distribution(effective_start_date, effective_end_date)
        
        # Total users for context on the analysis dashboard
        total_users = self.users_collection.count_documents({})

        return AnalysisStatistics(
            total_count=total,
            high_risk_count=high_risk,
            medium_risk_count=medium_risk,
            low_risk_count=low_risk,
            legitimate_count=legitimate,
            previous_total_count=previous_total,
            previous_scam_count=previous_scam_total,
            total_users=total_users,
            scam_categories_breakdown=categories,
            period=period,
            start_date=effective_start_date,
            end_date=effective_end_date,
            daily_counts=daily_counts,
            previous_daily_counts=previous_daily_counts,
            confidence_distribution=confidence_distribution,
            calculated_at=datetime.utcnow(),
        )
    
    def get_top_scam_categories(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        period: StatisticsPeriod = StatisticsPeriod.ALL_TIME,
        limit: int = 10
    ) -> List[ScamCategoryBreakdown]:
        """
        Get top scam categories by count.
        
        Args:
            start_date: Start of date range
            end_date: End of date range
            limit: Maximum number of categories to return
            
        Returns:
            List of ScamCategoryBreakdown entities
        """
        effective_start_date, effective_end_date = self._resolve_statistics_date_range(
            start_date=start_date,
            end_date=end_date,
            period=period,
        )

        # Build match stage
        match_stage = {"is_scam": True}
        date_filter = self._build_created_at_filter(effective_start_date, effective_end_date)
        if date_filter:
            match_stage["created_at"] = date_filter

        risk_bps_expression: Dict[str, Any] = {
            "$cond": [
                {"$gt": [{"$ifNull": ["$confidence_bps", 0]}, 0]},
                {"$ifNull": ["$confidence_bps", 0]},
                {"$multiply": [{"$ifNull": ["$scam_score", 0]}, 10000]},
            ]
        }
        
        pipeline = [
            {"$match": match_stage},
            {
                "$group": {
                    "_id": "$scam_type",
                    "count": {"$sum": 1},
                    "avg_risk_bps": {"$avg": risk_bps_expression},
                }
            },
            {"$sort": {"count": -1}},
            {"$limit": limit}
        ]
        
        results = list(self.analysis_collection.aggregate(pipeline))
        
        # Calculate total for percentages
        total = sum(r["count"] for r in results) if results else 1
        
        categories = []
        for r in results:
            category = r["_id"] or "Unknown"
            count = r["count"]
            percentage = (count / total) * 100 if total > 0 else 0

            avg_risk_bps = float(r.get("avg_risk_bps") or 0)
            avg_risk_percent = max(0.0, min(100.0, avg_risk_bps / 100.0))
            if avg_risk_bps >= 7000:
                severity = "high"
            elif avg_risk_bps >= 4000:
                severity = "medium"
            else:
                severity = "low"
            
            categories.append(ScamCategoryBreakdown(
                category=category,
                count=count,
                percentage=percentage,
                avg_risk_percent=avg_risk_percent,
                severity=severity
            ))
        
        return categories
    
    def _get_daily_analysis_counts(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get daily analysis counts for trend charts."""
        # Default to last 30 days if no range specified
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        pipeline = [
            {
                "$match": {
                    "created_at": {"$gte": start_date, "$lte": end_date}
                }
            },
            {
                "$group": {
                    "_id": {
                        "$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}
                    },
                    "total": {"$sum": 1},
                    "scams": {"$sum": {"$cond": ["$is_scam", 1, 0]}},
                    "legitimate": {"$sum": {"$cond": ["$is_scam", 0, 1]}}
                }
            },
            {"$sort": {"_id": 1}}
        ]
        
        results = list(self.analysis_collection.aggregate(pipeline))
        
        return [
            {
                "date": r["_id"],
                "total": r["total"],
                "scams": r["scams"],
                "legitimate": r["legitimate"]
            }
            for r in results
        ]

    def _get_confidence_distribution(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get confidence distribution buckets for analyses."""
        match_stage: Dict[str, Any] = {}
        date_filter = self._build_created_at_filter(start_date, end_date)
        if date_filter:
            match_stage["created_at"] = date_filter

        pipeline: List[Dict[str, Any]] = []
        if match_stage:
            pipeline.append({"$match": match_stage})

        pipeline.extend([
            {
                "$addFields": {
                    "confidence_percent": {
                        "$cond": [
                            {"$ne": ["$confidence_bps", None]},
                            {"$divide": ["$confidence_bps", 100]},
                            {
                                "$cond": [
                                    {"$ne": ["$scam_score", None]},
                                    {"$multiply": ["$scam_score", 100]},
                                    None,
                                ]
                            },
                        ]
                    }
                }
            },
            {
                "$addFields": {
                    "bucket": {
                        "$switch": {
                            "branches": [
                                {"case": {"$lte": ["$confidence_percent", 20]}, "then": "0-20"},
                                {
                                    "case": {
                                        "$and": [
                                            {"$gt": ["$confidence_percent", 20]},
                                            {"$lte": ["$confidence_percent", 40]},
                                        ]
                                    },
                                    "then": "21-40",
                                },
                                {
                                    "case": {
                                        "$and": [
                                            {"$gt": ["$confidence_percent", 40]},
                                            {"$lte": ["$confidence_percent", 60]},
                                        ]
                                    },
                                    "then": "41-60",
                                },
                                {
                                    "case": {
                                        "$and": [
                                            {"$gt": ["$confidence_percent", 60]},
                                            {"$lte": ["$confidence_percent", 80]},
                                        ]
                                    },
                                    "then": "61-80",
                                },
                                {
                                    "case": {
                                        "$and": [
                                            {"$gt": ["$confidence_percent", 80]},
                                            {"$lte": ["$confidence_percent", 100]},
                                        ]
                                    },
                                    "then": "81-100",
                                },
                            ],
                            "default": "unknown",
                        }
                    }
                }
            },
            {"$match": {"bucket": {"$ne": "unknown"}}},
            {
                "$group": {
                    "_id": "$bucket",
                    "count": {"$sum": 1}
                }
            },
        ])

        results = list(self.analysis_collection.aggregate(pipeline))
        counts_by_bucket = {r.get("_id"): r.get("count", 0) for r in results}

        ordered_buckets = ["0-20", "21-40", "41-60", "61-80", "81-100"]
        known_total = sum(counts_by_bucket.get(bucket, 0) for bucket in ordered_buckets)

        distribution = []
        for bucket in ordered_buckets:
            count = counts_by_bucket.get(bucket, 0)
            percentage = round((count / known_total) * 100, 2) if known_total > 0 else 0.0
            distribution.append({
                "bucket": bucket,
                "count": count,
                "percentage": percentage,
            })

        return distribution
    
    # ==================== User Statistics ====================
    
    def get_user_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        period: StatisticsPeriod = StatisticsPeriod.ALL_TIME
    ) -> UserStatistics:
        """
        Get aggregated user statistics.
        
        Args:
            start_date: Start of date range
            end_date: End of date range
            period: Time period for the statistics
            
        Returns:
            UserStatistics entity with aggregated data
        """
        effective_start_date, effective_end_date = self._resolve_statistics_date_range(
            start_date=self._to_utc_naive(start_date),
            end_date=self._to_utc_naive(end_date),
            period=period,
        )

        logger.debug(
            "Computing user statistics with period=%s, start=%s, end=%s",
            period.value,
            effective_start_date.isoformat() if effective_start_date else None,
            effective_end_date.isoformat() if effective_end_date else None,
        )

        # Total users count
        total_users = self.users_collection.count_documents({})
        
        # Verified vs unverified
        verified_count = self.users_collection.count_documents({"is_verified": True})
        unverified_count = total_users - verified_count
        
        # New users in period
        new_users_filter: Dict[str, Any] = {}
        if effective_start_date or effective_end_date:
            date_filter: Dict[str, Any] = {}
            if effective_start_date:
                date_filter["$gte"] = effective_start_date
            if effective_end_date:
                date_filter["$lte"] = effective_end_date
            new_users_filter["created_at"] = date_filter
        
        new_users_count = self.users_collection.count_documents(new_users_filter) if new_users_filter else 0
        logger.debug(
            "User statistics new-users query=%s result_count=%s",
            new_users_filter,
            new_users_count,
        )
        
        # Active accounts (accounts with is_active=True, i.e. not suspended/deactivated)
        active_users_count = self.users_collection.count_documents({"is_active": True})

        # Engaged users (users who performed analyses in the period)
        engaged_users_count = self._get_engaged_users_count(effective_start_date, effective_end_date)
        
        # Website visits
        visits, unique_visitors = self._get_visit_stats(effective_start_date, effective_end_date)
        
        # Total analyses by users
        total_analyses = self._get_total_analyses_count(effective_start_date, effective_end_date)
        avg_analyses = total_analyses / total_users if total_users > 0 else 0
        
        # Power users (>50 analyses)
        power_users_count = self._get_power_users_count()

        # Top power user in current period (highest detection usage)
        top_power_user = self._get_top_power_user(effective_start_date, effective_end_date)

        # Top 10 users most frequently targeted by scams
        top_susceptive_users = self._get_top_susceptive_users(effective_start_date, effective_end_date)
        
        # Daily signups trend
        daily_signups = self._get_daily_signups(effective_start_date, effective_end_date)
        
        # Daily visits trend
        daily_visits = self._get_daily_visits(effective_start_date, effective_end_date)
        
        return UserStatistics(
            total_users=total_users,
            new_users_count=new_users_count,
            active_users_count=active_users_count,
            engaged_users_count=engaged_users_count,
            verified_users_count=verified_count,
            unverified_users_count=unverified_count,
            website_visits=visits,
            unique_visitors=unique_visitors,
            total_analyses_by_users=total_analyses,
            avg_analyses_per_user=avg_analyses,
            power_users=power_users_count,
            top_power_user=top_power_user,
            top_susceptive_users=top_susceptive_users,
            period=period,
            start_date=effective_start_date,
            end_date=effective_end_date,
            daily_signups=daily_signups,
            daily_visits=daily_visits,
            calculated_at=datetime.utcnow(),
        )

    def _get_top_power_user(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get the single top user by detection usage in the selected timeframe."""
        match_stage: Dict[str, Any] = {"user_id": {"$exists": True, "$ne": None}}
        date_filter = self._build_created_at_filter(start_date, end_date)
        if date_filter:
            match_stage["created_at"] = date_filter

        pipeline = [
            {"$match": match_stage},
            {
                "$group": {
                    "_id": "$user_id",
                    "total_detections": {"$sum": 1},
                }
            },
            {"$sort": {"total_detections": -1}},
            {"$limit": 1},
        ]

        top_results = list(self.analysis_collection.aggregate(pipeline))
        logger.debug("Top power user aggregation result=%s", top_results)
        if not top_results or "_id" not in top_results[0]:
            return None

        top_result = top_results[0]
        user_id = str(top_result.get("_id"))
        total_detections = int(top_result.get("total_detections", 0))

        user_doc = self.users_collection.find_one(
            {
                "$or": [
                    {"user_id": user_id},
                    {"id": user_id},
                ]
            },
            {"username": 1, "email": 1, "user_id": 1},
        )

        if not user_doc:
            try:
                user_doc = self.users_collection.find_one(
                    {"_id": ObjectId(user_id)},
                    {"username": 1, "email": 1, "user_id": 1},
                )
            except Exception:
                user_doc = None

        return {
            "user_id": user_id,
            "username": user_doc.get("username") if user_doc else None,
            "email": user_doc.get("email") if user_doc else None,
            "total_detections": total_detections,
        }
    
    def _get_top_susceptive_users(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get top N users most frequently targeted by scams (is_scam=True)."""
        match_stage: Dict[str, Any] = {
            "user_id": {"$exists": True, "$ne": None},
            "is_scam": True,
        }
        date_filter = self._build_created_at_filter(start_date, end_date)
        if date_filter:
            match_stage["created_at"] = date_filter

        pipeline = [
            {"$match": match_stage},
            {
                "$group": {
                    "_id": "$user_id",
                    "scam_encounters": {"$sum": 1},
                }
            },
            {"$sort": {"scam_encounters": -1}},
            {"$limit": limit},
        ]

        results = list(self.analysis_collection.aggregate(pipeline))
        logger.debug("Top susceptive users aggregation result=%s", results)

        users: List[Dict[str, Any]] = []
        for r in results:
            user_id = str(r.get("_id"))
            scam_encounters = int(r.get("scam_encounters", 0))

            # Look up the actual username
            user_doc = self.users_collection.find_one(
                {
                    "$or": [
                        {"user_id": user_id},
                        {"id": user_id},
                    ]
                },
                {"username": 1, "email": 1, "user_id": 1},
            )
            if not user_doc:
                try:
                    user_doc = self.users_collection.find_one(
                        {"_id": ObjectId(user_id)},
                        {"username": 1, "email": 1, "user_id": 1},
                    )
                except Exception:
                    user_doc = None

            users.append({
                "user_id": user_id,
                "username": user_doc.get("username") if user_doc else None,
                "email": user_doc.get("email") if user_doc else None,
                "scam_encounters": scam_encounters,
            })

        return users

    def _get_engaged_users_count(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> int:
        """Get count of users who performed analyses in the period (engaged users)."""
        match_stage: Dict[str, Any] = {"user_id": {"$exists": True, "$ne": None}}
        if start_date or end_date:
            date_filter: Dict[str, Any] = {}
            if start_date:
                date_filter["$gte"] = start_date
            if end_date:
                date_filter["$lte"] = end_date
            match_stage["created_at"] = date_filter
        
        pipeline = [
            {"$match": match_stage},
            {"$group": {"_id": "$user_id"}},
            {"$count": "engaged_users"}
        ]
        
        result = list(self.analysis_collection.aggregate(pipeline))
        return result[0]["engaged_users"] if result else 0
    
    def _get_power_users_count(self, min_analyses: int = 50) -> int:
        """
        Get count of power users (users with more than min_analyses).
        
        Args:
            min_analyses: Minimum number of analyses to be considered a power user
            
        Returns:
            Count of power users
        """
        pipeline = [
            {"$match": {"user_id": {"$exists": True, "$ne": None}}},
            {"$group": {"_id": "$user_id", "count": {"$sum": 1}}},
            {"$match": {"count": {"$gt": min_analyses}}},
            {"$count": "power_users"}
        ]
        
        result = list(self.analysis_collection.aggregate(pipeline))
        return result[0]["power_users"] if result else 0
    
    def _get_total_analyses_count(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> int:
        """Get total analysis count for the period."""
        filter_query: Dict[str, Any] = {}
        if start_date or end_date:
            date_filter: Dict[str, Any] = {}
            if start_date:
                date_filter["$gte"] = start_date
            if end_date:
                date_filter["$lte"] = end_date
            filter_query["created_at"] = date_filter
        
        return self.analysis_collection.count_documents(filter_query)
    
    def _get_visit_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Tuple[int, int]:
        """Get website visit statistics."""
        try:
            filter_query: Dict[str, Any] = {}
            if start_date or end_date:
                date_filter: Dict[str, Any] = {}
                if start_date:
                    date_filter["$gte"] = start_date
                if end_date:
                    date_filter["$lte"] = end_date
                filter_query["timestamp"] = date_filter
            
            # Total visits
            total_visits = self.visits_collection.count_documents(filter_query)
            
            # Unique visitors (by session_id or ip)
            pipeline = [
                {"$match": filter_query} if filter_query else {"$match": {}},
                {"$group": {"_id": {"$ifNull": ["$session_id", "$ip_address"]}}},
                {"$count": "unique"}
            ]
            result = list(self.visits_collection.aggregate(pipeline))
            unique_visitors = result[0]["unique"] if result else 0
            
            return total_visits, unique_visitors
        except Exception as e:
            logger.warning(f"Could not get visit stats: {e}")
            return 0, 0
    
    def _get_daily_signups(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get daily signup counts."""
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        pipeline = [
            {
                "$match": {
                    "created_at": {"$gte": start_date, "$lte": end_date}
                }
            },
            {
                "$group": {
                    "_id": {
                        "$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}
                    },
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"_id": 1}}
        ]
        
        results = list(self.users_collection.aggregate(pipeline))
        return [{"date": r["_id"], "count": r["count"]} for r in results]
    
    def _get_daily_visits(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get daily visit counts."""
        try:
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            pipeline = [
                {
                    "$match": {
                        "timestamp": {"$gte": start_date, "$lte": end_date}
                    }
                },
                {
                    "$group": {
                        "_id": {
                            "$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}
                        },
                        "count": {"$sum": 1}
                    }
                },
                {"$sort": {"_id": 1}}
            ]
            
            results = list(self.visits_collection.aggregate(pipeline))
            return [{"date": r["_id"], "count": r["count"]} for r in results]
        except Exception:
            return []
    
    # ==================== User Reports ====================
    
    def create_report(self, report: UserReport) -> UserReport:
        """
        Create a new user report.
        
        Args:
            report: UserReport entity to create
            
        Returns:
            Created report with generated ID
        """
        doc = {
            "report_id": report.report_id,
            "user_id": report.user_id,
            "user_email": report.user_email,
            "report_type": report.report_type.value,
            "title": report.title,
            "description": report.description,
            "analysis_id": report.analysis_id,
            "analysis_ref_id": report.analysis_ref_id,
            "status": report.status.value,
            "assigned_to": report.assigned_to,
            "resolution_notes": report.resolution_notes,
            "created_at": report.created_at,
            "updated_at": report.updated_at,
            "resolved_at": report.resolved_at,
        }
        
        result = self.reports_collection.insert_one(doc)
        report.id = str(result.inserted_id)
        return report
    
    def get_report_by_id(self, report_id: str) -> Optional[UserReport]:
        """
        Get a report by its ID.
        
        Args:
            report_id: Report ID (either _id or report_id)
            
        Returns:
            UserReport entity or None
        """
        # Try finding by report_id first
        doc = self.reports_collection.find_one({"report_id": report_id})
        
        # Try by ObjectId if not found
        if not doc:
            try:
                doc = self.reports_collection.find_one({"_id": ObjectId(report_id)})
            except Exception:
                pass
        
        if not doc:
            return None
        
        return self._document_to_report(doc)
    
    def get_reports(
        self,
        status: Optional[ReportStatus] = None,
        user_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[UserReport], int]:
        """
        Get reports with filtering and pagination.
        
        Args:
            status: Filter by status
            user_id: Filter by user ID
            limit: Maximum results
            offset: Skip count
            
        Returns:
            Tuple of (reports list, total count)
        """
        filter_query: Dict[str, Any] = {}
        if status:
            filter_query["status"] = status.value
        if user_id:
            filter_query["user_id"] = user_id
        
        total = self.reports_collection.count_documents(filter_query)
        
        docs = self.reports_collection.find(filter_query)\
            .sort("created_at", DESCENDING)\
            .skip(offset)\
            .limit(limit)
        
        reports = [self._document_to_report(doc) for doc in docs]
        return reports, total
    
    def update_report_status(
        self,
        report_id: str,
        status: ReportStatus,
        resolution_notes: Optional[str] = None,
        assigned_to: Optional[str] = None
    ) -> UserReport:
        """
        Update a report's status.
        
        Args:
            report_id: Report ID
            status: New status
            resolution_notes: Optional resolution notes
            assigned_to: Optional admin user ID
            
        Returns:
            Updated UserReport entity
            
        Raises:
            ReportNotFoundError: If report not found
        """
        update_doc = {
            "status": status.value,
            "updated_at": datetime.utcnow(),
        }
        
        if resolution_notes is not None:
            update_doc["resolution_notes"] = resolution_notes
        
        if assigned_to is not None:
            update_doc["assigned_to"] = assigned_to
        
        if status in [ReportStatus.RESOLVED, ReportStatus.DISMISSED]:
            update_doc["resolved_at"] = datetime.utcnow()
        
        # Try updating by report_id first
        result = self.reports_collection.find_one_and_update(
            {"report_id": report_id},
            {"$set": update_doc},
            return_document=True
        )
        
        # Try by ObjectId if not found
        if not result:
            try:
                result = self.reports_collection.find_one_and_update(
                    {"_id": ObjectId(report_id)},
                    {"$set": update_doc},
                    return_document=True
                )
            except Exception:
                pass
        
        if not result:
            raise ReportNotFoundError(f"Report {report_id} not found")
        
        return self._document_to_report(result)
    
    def _document_to_report(self, doc: Dict[str, Any]) -> UserReport:
        """Convert MongoDB document to UserReport entity."""
        report_type_raw = str(doc.get("report_type", "other")).strip().lower()
        report_type_aliases = {
            "low_confidence": ReportType.OTHER,
            "high_confidence": ReportType.OTHER,
        }
        try:
            report_type = ReportType(report_type_raw)
        except ValueError:
            report_type = report_type_aliases.get(report_type_raw, ReportType.OTHER)
            logger.warning(
                "Unknown report_type '%s' for report_id=%s. Falling back to '%s'.",
                report_type_raw,
                doc.get("report_id", str(doc.get("_id", "unknown"))),
                report_type.value,
            )

        return UserReport(
            id=str(doc["_id"]),
            report_id=doc.get("report_id", str(doc["_id"])),
            user_id=doc.get("user_id", ""),
            user_email=doc.get("user_email"),
            report_type=report_type,
            title=doc.get("title", ""),
            description=doc.get("description", ""),
            analysis_id=doc.get("analysis_id"),
            analysis_ref_id=doc.get("analysis_ref_id"),
            status=ReportStatus(doc.get("status", "pending")),
            assigned_to=doc.get("assigned_to"),
            resolution_notes=doc.get("resolution_notes"),
            created_at=doc.get("created_at", datetime.utcnow()),
            updated_at=doc.get("updated_at", datetime.utcnow()),
            resolved_at=doc.get("resolved_at"),
        )
    
    # ==================== Admin Activity Logs ====================
    
    def log_admin_activity(self, log: AdminActivityLog) -> AdminActivityLog:
        """
        Create an admin activity log entry.
        
        Args:
            log: AdminActivityLog entity
            
        Returns:
            Created log with generated ID
        """
        doc = log.to_dict()
        doc["created_at"] = log.created_at  # Ensure datetime, not string
        
        result = self.activity_logs_collection.insert_one(doc)
        log.id = str(result.inserted_id)
        return log
    
    def get_activity_logs(
        self,
        admin_user_id: Optional[str] = None,
        action: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[AdminActivityLog], int]:
        """
        Get admin activity logs with filtering.
        
        Args:
            admin_user_id: Filter by admin user
            action: Filter by action type
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum results
            offset: Skip count
            
        Returns:
            Tuple of (logs list, total count)
        """
        filter_query: Dict[str, Any] = {}
        
        if admin_user_id:
            filter_query["admin_user_id"] = admin_user_id
        if action:
            filter_query["action"] = action
        if start_date or end_date:
            date_filter: Dict[str, Any] = {}
            if start_date:
                date_filter["$gte"] = start_date
            if end_date:
                date_filter["$lte"] = end_date
            filter_query["created_at"] = date_filter
        
        total = self.activity_logs_collection.count_documents(filter_query)
        
        docs = self.activity_logs_collection.find(filter_query)\
            .sort("created_at", DESCENDING)\
            .skip(offset)\
            .limit(limit)
        
        logs = [self._document_to_activity_log(doc) for doc in docs]
        return logs, total
    
    def _document_to_activity_log(self, doc: Dict[str, Any]) -> AdminActivityLog:
        """Convert MongoDB document to AdminActivityLog entity."""
        return AdminActivityLog(
            id=str(doc["_id"]),
            log_id=doc.get("log_id", str(doc["_id"])),
            admin_user_id=doc.get("admin_user_id", ""),
            admin_email=doc.get("admin_email"),
            action=doc.get("action", ""),
            resource_type=doc.get("resource_type", ""),
            resource_id=doc.get("resource_id"),
            details=doc.get("details", {}),
            ip_address=doc.get("ip_address"),
            user_agent=doc.get("user_agent"),
            created_at=doc.get("created_at", datetime.utcnow()),
        )
