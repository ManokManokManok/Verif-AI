"""
Model Health Use Case

Use case for retrieving current model health metrics including
GPU/CPU utilization, memory usage, and model performance statistics.
"""

from typing import Protocol, Optional
from dataclasses import dataclass
from datetime import datetime

from ...domain.admin_entities import ModelHealthMetrics, MetricsCollectionError


class MetricsCollector(Protocol):
    """Protocol for system metrics collection."""
    def collect_metrics(self) -> ModelHealthMetrics: ...


@dataclass
class ModelHealthResult:
    """Result object for model health use case."""
    metrics: ModelHealthMetrics
    success: bool
    error_message: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        result = {
            "success": self.success,
        }
        if self.success:
            result["data"] = self.metrics.to_dict()
        else:
            result["error"] = self.error_message
        return result


class GetModelHealthUseCase:
    """
    Use case for retrieving current model health metrics.
    
    Retrieves system metrics including:
    - GPU utilization and memory
    - CPU utilization
    - System memory usage
    - Token processing metrics
    - Model inference speed
    - System uptime
    
    This use case is read-only and does not modify any state.
    """
    
    def __init__(self, metrics_collector: MetricsCollector):
        """
        Initialize the use case.
        
        Args:
            metrics_collector: Infrastructure component for collecting system metrics
        """
        self._metrics_collector = metrics_collector
    
    def execute(self) -> ModelHealthResult:
        """
        Execute the use case to retrieve current model health metrics.
        
        Returns:
            ModelHealthResult containing metrics or error information
        """
        try:
            metrics = self._metrics_collector.collect_metrics()
            return ModelHealthResult(
                metrics=metrics,
                success=True
            )
        except MetricsCollectionError as e:
            return ModelHealthResult(
                metrics=None,
                success=False,
                error_message=str(e)
            )
        except Exception as e:
            return ModelHealthResult(
                metrics=None,
                success=False,
                error_message=f"Unexpected error collecting metrics: {str(e)}"
            )
    
    def get_metrics_summary(self) -> dict:
        """
        Get a simplified summary of model health.
        
        Returns:
            Dict with key health indicators
        """
        result = self.execute()
        
        if not result.success:
            return {
                "status": "error",
                "message": result.error_message
            }
        
        metrics = result.metrics
        
        # Determine overall health status
        status = "healthy"
        warnings = []
        
        if metrics.cpu_usage_percent > 90:
            status = "warning"
            warnings.append("High CPU usage")
        
        if metrics.memory_usage_percent > 90:
            status = "warning"
            warnings.append("High memory usage")
        
        if metrics.is_gpu_available and metrics.gpu_usage_percent > 95:
            status = "warning"
            warnings.append("High GPU usage")
        
        if metrics.is_gpu_available and metrics.gpu_memory_usage_percent > 95:
            status = "critical"
            warnings.append("GPU memory nearly full")
        
        return {
            "status": status,
            "warnings": warnings,
            "cpu_percent": metrics.cpu_usage_percent,
            "memory_percent": metrics.memory_usage_percent,
            "gpu_percent": metrics.gpu_usage_percent if metrics.is_gpu_available else None,
            "gpu_available": metrics.is_gpu_available,
            "uptime": metrics.uptime_formatted,
            "requests_today": metrics.requests_today,
        }
