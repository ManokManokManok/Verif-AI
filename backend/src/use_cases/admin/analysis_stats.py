"""
Analysis Statistics Use Cases

Use cases for retrieving analysis statistics including total analyses,
risk level breakdowns, and scam category distributions.
"""

from typing import Protocol, Optional, List
from dataclasses import dataclass
from datetime import datetime

from ...domain.admin_entities import (
    AnalysisStatistics,
    ScamCategoryBreakdown,
    StatisticsPeriod,
)


class AdminRepository(Protocol):
    """Protocol for admin data repository."""
    def get_analysis_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        period: StatisticsPeriod = StatisticsPeriod.ALL_TIME
    ) -> AnalysisStatistics: ...
    
    def get_top_scam_categories(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 10
    ) -> List[ScamCategoryBreakdown]: ...


@dataclass
class AnalysisStatisticsResult:
    """Result object for analysis statistics use case."""
    statistics: Optional[AnalysisStatistics]
    success: bool
    error_message: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        result = {"success": self.success}
        if self.success and self.statistics:
            result["data"] = self.statistics.to_dict()
        else:
            result["error"] = self.error_message
        return result


@dataclass
class TopCategoriesResult:
    """Result object for top scam categories use case."""
    categories: List[ScamCategoryBreakdown]
    success: bool
    error_message: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        result = {"success": self.success}
        if self.success:
            result["data"] = [cat.to_dict() for cat in self.categories]
        else:
            result["error"] = self.error_message
        return result


class GetAnalysisStatisticsUseCase:
    """
    Use case for retrieving analysis statistics.
    
    Retrieves aggregated statistics including:
    - Total analyses count
    - High/medium/low risk breakdown
    - Legitimate vs scam analysis counts
    - Daily trend data
    - Time period filtering
    
    This use case is read-only and performs aggregation queries
    on the analysis results collection.
    """
    
    def __init__(self, admin_repository: AdminRepository):
        """
        Initialize the use case.
        
        Args:
            admin_repository: Repository for admin data aggregations
        """
        self._admin_repository = admin_repository
    
    def execute(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        period: StatisticsPeriod = StatisticsPeriod.ALL_TIME
    ) -> AnalysisStatisticsResult:
        """
        Execute the use case to retrieve analysis statistics.
        
        Args:
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)
            period: Time period for grouping
            
        Returns:
            AnalysisStatisticsResult containing statistics or error
        """
        try:
            # Validate date range
            if start_date and end_date and start_date > end_date:
                return AnalysisStatisticsResult(
                    statistics=None,
                    success=False,
                    error_message="Start date must be before end date"
                )
            
            statistics = self._admin_repository.get_analysis_statistics(
                start_date=start_date,
                end_date=end_date,
                period=period
            )
            
            return AnalysisStatisticsResult(
                statistics=statistics,
                success=True
            )
        except Exception as e:
            return AnalysisStatisticsResult(
                statistics=None,
                success=False,
                error_message=f"Failed to retrieve analysis statistics: {str(e)}"
            )
    
    def get_summary(
        self,
        period: StatisticsPeriod = StatisticsPeriod.ALL_TIME
    ) -> dict:
        """
        Get a simplified summary of analysis statistics.
        
        Args:
            period: Time period for statistics
            
        Returns:
            Dict with key statistics
        """
        result = self.execute(period=period)
        
        if not result.success:
            return {"error": result.error_message}
        
        stats = result.statistics
        total = stats.total_count or 1  # Avoid division by zero
        
        return {
            "total_analyses": stats.total_count,
            "high_risk_count": stats.high_risk_count,
            "high_risk_percent": round((stats.high_risk_count / total) * 100, 1),
            "medium_risk_count": stats.medium_risk_count,
            "medium_risk_percent": round((stats.medium_risk_count / total) * 100, 1),
            "low_risk_count": stats.low_risk_count,
            "low_risk_percent": round((stats.low_risk_count / total) * 100, 1),
            "legitimate_count": stats.legitimate_count,
            "legitimate_percent": round((stats.legitimate_count / total) * 100, 1),
            "scam_detection_rate": round(
                ((stats.high_risk_count + stats.medium_risk_count + stats.low_risk_count) / total) * 100, 1
            ),
        }


class GetTopScamCategoriesUseCase:
    """
    Use case for retrieving top scam categories.
    
    Returns a ranked list of scam categories by occurrence count,
    useful for identifying common scam patterns.
    """
    
    def __init__(self, admin_repository: AdminRepository):
        """
        Initialize the use case.
        
        Args:
            admin_repository: Repository for admin data aggregations
        """
        self._admin_repository = admin_repository
    
    def execute(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 10
    ) -> TopCategoriesResult:
        """
        Execute the use case to retrieve top scam categories.
        
        Args:
            start_date: Start of date range
            end_date: End of date range
            limit: Maximum number of categories to return
            
        Returns:
            TopCategoriesResult containing categories or error
        """
        try:
            # Validate limit
            if limit < 1:
                limit = 1
            elif limit > 50:
                limit = 50
            
            categories = self._admin_repository.get_top_scam_categories(
                start_date=start_date,
                end_date=end_date,
                limit=limit
            )
            
            return TopCategoriesResult(
                categories=categories,
                success=True
            )
        except Exception as e:
            return TopCategoriesResult(
                categories=[],
                success=False,
                error_message=f"Failed to retrieve scam categories: {str(e)}"
            )
