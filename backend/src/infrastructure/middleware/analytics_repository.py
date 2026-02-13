"""
Analytics Repository

MongoDB repository for website analytics data including page visits,
unique visitors, and custom events tracking.
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from pymongo import MongoClient, DESCENDING, ASCENDING
from pymongo.collection import Collection
from pymongo.database import Database
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

# Global repository instance
_analytics_repository = None


@dataclass
class VisitStatistics:
    """Statistics about website visits."""
    total_visits: int
    unique_visitors: int
    authenticated_visits: int
    anonymous_visits: int
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_visits': self.total_visits,
            'unique_visitors': self.unique_visitors,
            'authenticated_visits': self.authenticated_visits,
            'anonymous_visits': self.anonymous_visits,
            'period_start': self.period_start.isoformat() if self.period_start else None,
            'period_end': self.period_end.isoformat() if self.period_end else None,
        }


@dataclass
class PageVisitStats:
    """Statistics for individual pages."""
    path: str
    visit_count: int
    unique_visitors: int
    avg_response_time_ms: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'path': self.path,
            'visit_count': self.visit_count,
            'unique_visitors': self.unique_visitors,
            'avg_response_time_ms': round(self.avg_response_time_ms, 2),
        }


@dataclass
class DeviceBreakdown:
    """Device type breakdown statistics."""
    desktop: int
    mobile: int
    tablet: int
    unknown: int
    
    def to_dict(self) -> Dict[str, Any]:
        total = self.desktop + self.mobile + self.tablet + self.unknown
        return {
            'desktop': self.desktop,
            'mobile': self.mobile,
            'tablet': self.tablet,
            'unknown': self.unknown,
            'total': total,
            'percentages': {
                'desktop': round(self.desktop / total * 100, 1) if total > 0 else 0,
                'mobile': round(self.mobile / total * 100, 1) if total > 0 else 0,
                'tablet': round(self.tablet / total * 100, 1) if total > 0 else 0,
            }
        }


@dataclass  
class TimeSeriesPoint:
    """Single point in time series data."""
    date: datetime
    count: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'date': self.date.isoformat(),
            'count': self.count,
        }


class AnalyticsRepository:
    """
    MongoDB repository for website analytics.
    
    Provides methods for:
    - Recording page visits
    - Aggregating visit statistics
    - Tracking unique visitors
    - Page popularity analysis
    - Time series data for graphs
    """
    
    def __init__(self, client: MongoClient, database_name: str):
        self.db: Database = client[database_name]
        self.visits_collection: Collection = self.db.website_visits
        self.events_collection: Collection = self.db.analytics_events
        self._ensure_indexes()
    
    def _ensure_indexes(self) -> None:
        """Create indexes for efficient analytics queries."""
        # Visit indexes
        self.visits_collection.create_index("timestamp")
        self.visits_collection.create_index("path")
        self.visits_collection.create_index("anonymous_ip")
        self.visits_collection.create_index("user_id")
        self.visits_collection.create_index("device_type")
        self.visits_collection.create_index([("timestamp", DESCENDING)])
        self.visits_collection.create_index([("path", ASCENDING), ("timestamp", DESCENDING)])
        
        # Compound index for common queries
        self.visits_collection.create_index([
            ("timestamp", DESCENDING),
            ("path", ASCENDING),
            ("device_type", ASCENDING)
        ])
        
        # Events indexes
        self.events_collection.create_index("timestamp")
        self.events_collection.create_index("event_name")
    
    # ==================== Write Operations ====================
    
    def track_visit(self, visit_data: Dict[str, Any]) -> str:
        """
        Record a single page visit.
        
        Args:
            visit_data: Dictionary containing visit information
            
        Returns:
            Inserted document ID
        """
        result = self.visits_collection.insert_one(visit_data)
        return str(result.inserted_id)
    
    def bulk_insert_visits(self, visits: List[Dict[str, Any]]) -> int:
        """
        Bulk insert multiple visits for efficiency.
        
        Args:
            visits: List of visit data dictionaries
            
        Returns:
            Number of inserted documents
        """
        if not visits:
            return 0
        result = self.visits_collection.insert_many(visits, ordered=False)
        return len(result.inserted_ids)
    
    def track_custom_event(
        self,
        event_name: str,
        timestamp: datetime,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Track a custom analytics event.
        
        Args:
            event_name: Name of the event
            timestamp: When the event occurred
            metadata: Additional event data
            
        Returns:
            Inserted document ID
        """
        event = {
            'event_name': event_name,
            'timestamp': timestamp,
            'metadata': metadata or {},
        }
        result = self.events_collection.insert_one(event)
        return str(result.inserted_id)
    
    # ==================== Read Operations ====================
    
    def get_visit_count(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> int:
        """Get total visit count for a date range."""
        query = self._build_date_query(start_date, end_date)
        return self.visits_collection.count_documents(query)
    
    def get_unique_visitors(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> int:
        """Get count of unique visitors (by anonymous IP)."""
        query = self._build_date_query(start_date, end_date)
        pipeline = [
            {"$match": query} if query else {"$match": {}},
            {"$group": {"_id": "$anonymous_ip"}},
            {"$count": "unique_visitors"}
        ]
        result = list(self.visits_collection.aggregate(pipeline))
        return result[0]['unique_visitors'] if result else 0
    
    def get_visit_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> VisitStatistics:
        """
        Get comprehensive visit statistics.
        
        Args:
            start_date: Start of date range
            end_date: End of date range
            
        Returns:
            VisitStatistics with aggregated data
        """
        query = self._build_date_query(start_date, end_date)
        
        pipeline = [
            {"$match": query} if query else {"$match": {}},
            {
                "$facet": {
                    "total": [{"$count": "count"}],
                    "unique_ips": [
                        {"$group": {"_id": "$anonymous_ip"}},
                        {"$count": "count"}
                    ],
                    "authenticated": [
                        {"$match": {"is_authenticated": True}},
                        {"$count": "count"}
                    ],
                    "anonymous": [
                        {"$match": {"is_authenticated": False}},
                        {"$count": "count"}
                    ]
                }
            }
        ]
        
        result = list(self.visits_collection.aggregate(pipeline))
        
        if not result:
            return VisitStatistics(
                total_visits=0,
                unique_visitors=0,
                authenticated_visits=0,
                anonymous_visits=0,
                period_start=start_date,
                period_end=end_date
            )
        
        facets = result[0]
        return VisitStatistics(
            total_visits=facets['total'][0]['count'] if facets['total'] else 0,
            unique_visitors=facets['unique_ips'][0]['count'] if facets['unique_ips'] else 0,
            authenticated_visits=facets['authenticated'][0]['count'] if facets['authenticated'] else 0,
            anonymous_visits=facets['anonymous'][0]['count'] if facets['anonymous'] else 0,
            period_start=start_date,
            period_end=end_date
        )
    
    def get_visits_by_page(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 10
    ) -> List[PageVisitStats]:
        """
        Get visit statistics grouped by page path.
        
        Args:
            start_date: Start of date range
            end_date: End of date range
            limit: Maximum number of pages to return
            
        Returns:
            List of PageVisitStats sorted by visit count
        """
        query = self._build_date_query(start_date, end_date)
        
        pipeline = [
            {"$match": query} if query else {"$match": {}},
            {
                "$group": {
                    "_id": "$path",
                    "visit_count": {"$sum": 1},
                    "unique_ips": {"$addToSet": "$anonymous_ip"},
                    "avg_response_time": {"$avg": "$response_time_ms"}
                }
            },
            {
                "$project": {
                    "path": "$_id",
                    "visit_count": 1,
                    "unique_visitors": {"$size": "$unique_ips"},
                    "avg_response_time": {"$ifNull": ["$avg_response_time", 0]}
                }
            },
            {"$sort": {"visit_count": -1}},
            {"$limit": limit}
        ]
        
        results = list(self.visits_collection.aggregate(pipeline))
        return [
            PageVisitStats(
                path=r['path'],
                visit_count=r['visit_count'],
                unique_visitors=r['unique_visitors'],
                avg_response_time_ms=r['avg_response_time'] or 0
            )
            for r in results
        ]
    
    def get_device_breakdown(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> DeviceBreakdown:
        """
        Get breakdown of visits by device type.
        
        Args:
            start_date: Start of date range
            end_date: End of date range
            
        Returns:
            DeviceBreakdown with counts per device type
        """
        query = self._build_date_query(start_date, end_date)
        
        pipeline = [
            {"$match": query} if query else {"$match": {}},
            {
                "$group": {
                    "_id": "$device_type",
                    "count": {"$sum": 1}
                }
            }
        ]
        
        results = list(self.visits_collection.aggregate(pipeline))
        device_counts = {r['_id']: r['count'] for r in results}
        
        return DeviceBreakdown(
            desktop=device_counts.get('desktop', 0),
            mobile=device_counts.get('mobile', 0),
            tablet=device_counts.get('tablet', 0),
            unknown=device_counts.get('unknown', 0)
        )
    
    def get_visits_time_series(
        self,
        start_date: datetime,
        end_date: datetime,
        granularity: str = 'day'
    ) -> List[TimeSeriesPoint]:
        """
        Get visit counts over time for graphing.
        
        Args:
            start_date: Start of date range
            end_date: End of date range
            granularity: 'hour', 'day', 'week', or 'month'
            
        Returns:
            List of TimeSeriesPoint for graphing
        """
        query = self._build_date_query(start_date, end_date)
        
        # Define date grouping based on granularity
        date_format = {
            'hour': {
                'year': {"$year": "$timestamp"},
                'month': {"$month": "$timestamp"},
                'day': {"$dayOfMonth": "$timestamp"},
                'hour': {"$hour": "$timestamp"}
            },
            'day': {
                'year': {"$year": "$timestamp"},
                'month': {"$month": "$timestamp"},
                'day': {"$dayOfMonth": "$timestamp"}
            },
            'week': {
                'year': {"$year": "$timestamp"},
                'week': {"$week": "$timestamp"}
            },
            'month': {
                'year': {"$year": "$timestamp"},
                'month': {"$month": "$timestamp"}
            }
        }
        
        group_id = date_format.get(granularity, date_format['day'])
        
        pipeline = [
            {"$match": query} if query else {"$match": {}},
            {
                "$group": {
                    "_id": group_id,
                    "count": {"$sum": 1},
                    "min_timestamp": {"$min": "$timestamp"}
                }
            },
            {"$sort": {"min_timestamp": 1}}
        ]
        
        results = list(self.visits_collection.aggregate(pipeline))
        return [
            TimeSeriesPoint(
                date=r['min_timestamp'],
                count=r['count']
            )
            for r in results
        ]
    
    def get_recent_visits(
        self,
        limit: int = 50,
        path_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get most recent visits for monitoring.
        
        Args:
            limit: Maximum number of visits to return
            path_filter: Optional path to filter by
            
        Returns:
            List of recent visit documents
        """
        query = {}
        if path_filter:
            query['path'] = {'$regex': path_filter, '$options': 'i'}
        
        cursor = self.visits_collection.find(
            query,
            {'_id': 0}
        ).sort('timestamp', DESCENDING).limit(limit)
        
        return list(cursor)
    
    def get_hourly_traffic_pattern(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[int, int]:
        """
        Get traffic patterns by hour of day.
        
        Args:
            start_date: Start of date range
            end_date: End of date range
            
        Returns:
            Dictionary mapping hour (0-23) to visit count
        """
        query = self._build_date_query(start_date, end_date)
        
        pipeline = [
            {"$match": query} if query else {"$match": {}},
            {
                "$group": {
                    "_id": {"$hour": "$timestamp"},
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"_id": 1}}
        ]
        
        results = list(self.visits_collection.aggregate(pipeline))
        # Initialize all hours with 0
        hourly = {i: 0 for i in range(24)}
        for r in results:
            hourly[r['_id']] = r['count']
        return hourly
    
    def get_referrer_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get top referrers.
        
        Args:
            start_date: Start of date range
            end_date: End of date range
            limit: Maximum number of referrers to return
            
        Returns:
            List of referrer statistics
        """
        query = self._build_date_query(start_date, end_date)
        query['referrer'] = {'$ne': '', '$exists': True}
        
        pipeline = [
            {"$match": query},
            {
                "$group": {
                    "_id": "$referrer",
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"count": -1}},
            {"$limit": limit}
        ]
        
        results = list(self.visits_collection.aggregate(pipeline))
        return [
            {'referrer': r['_id'], 'count': r['count']}
            for r in results
        ]
    
    # ==================== Helper Methods ====================
    
    def _build_date_query(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Build MongoDB query for date range filtering."""
        if not start_date and not end_date:
            return {}
        
        date_filter = {}
        if start_date:
            date_filter['$gte'] = start_date
        if end_date:
            date_filter['$lte'] = end_date
        
        return {'timestamp': date_filter}
    
    def cleanup_old_visits(self, days_to_keep: int = 90) -> int:
        """
        Remove visits older than specified days (for data retention).
        
        Args:
            days_to_keep: Number of days of data to retain
            
        Returns:
            Number of deleted documents
        """
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        result = self.visits_collection.delete_many({
            'timestamp': {'$lt': cutoff_date}
        })
        logger.info(f"Cleaned up {result.deleted_count} old visit records")
        return result.deleted_count


def get_analytics_repository() -> Optional[AnalyticsRepository]:
    """Get or create the global analytics repository instance."""
    global _analytics_repository
    
    if _analytics_repository is None:
        try:
            from ..mongodb.connection import get_mongo_client, get_database_name
            client = get_mongo_client()
            db_name = get_database_name()
            _analytics_repository = AnalyticsRepository(client, db_name)
        except Exception as e:
            logger.error(f"Failed to initialize analytics repository: {e}")
            return None
    
    return _analytics_repository


def reset_analytics_repository():
    """Reset the global repository (for testing)."""
    global _analytics_repository
    _analytics_repository = None
