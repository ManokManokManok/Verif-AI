"""
System Metrics Collector

Infrastructure component for collecting system health metrics including
CPU, memory, GPU usage, and model performance statistics.
"""

import os
import sys
import time
import logging
import platform as platform_lib
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from functools import lru_cache

from ...domain.admin_entities import ModelHealthMetrics, MetricsCollectionError

logger = logging.getLogger(__name__)

# Track application start time for uptime calculation
_APP_START_TIME = time.time()

# In-memory counters for model metrics (would be replaced by Redis in production)
_model_metrics = {
    "token_count_today": 0,
    "token_count_total": 0,
    "requests_today": 0,
    "requests_total": 0,
    "processing_times_ms": [],  # Recent processing times for averaging
    "last_reset_date": datetime.utcnow().date(),
}


def _try_import_psutil():
    """Try to import psutil, return None if not available."""
    try:
        import psutil
        return psutil
    except ImportError:
        logger.warning("psutil not installed. CPU/Memory metrics will use fallback values.")
        return None


def _try_import_pynvml():
    """Try to import pynvml for NVIDIA GPU metrics."""
    try:
        import pynvml  # type: ignore[import-not-found]
        pynvml.nvmlInit()
        return pynvml
    except ImportError:
        logger.info("pynvml not installed. GPU metrics will not be available.")
        return None
    except Exception as e:
        logger.info(f"NVIDIA driver not available: {e}. GPU metrics will not be available.")
        return None


class SystemMetricsCollector:
    """
    Collects system metrics for model health monitoring.
    
    Provides CPU, memory, and GPU utilization metrics along with
    model performance statistics like token counts and processing speeds.
    """
    
    def __init__(self, model_name: str = "verif-ai-bert"):
        """
        Initialize the metrics collector.
        
        Args:
            model_name: Name of the AI model being monitored
        """
        self.model_name = model_name
        self._psutil = _try_import_psutil()
        self._pynvml = _try_import_pynvml()
        self._gpu_handle = None
        self._active_sessions = 0  # Track active sessions
        self._cache_stats = {"hits": 0, "misses": 0, "size_mb": 0}  # Cache stats
        
        # Initialize GPU handle if available
        if self._pynvml:
            try:
                self._gpu_handle = self._pynvml.nvmlDeviceGetHandleByIndex(0)
            except Exception as e:
                logger.warning(f"Could not get GPU handle: {e}")
                self._pynvml = None
    
    def collect_metrics(self) -> ModelHealthMetrics:
        """
        Collect all system metrics.
        
        Returns:
            ModelHealthMetrics entity with current system state
            
        Raises:
            MetricsCollectionError: If critical metrics cannot be collected
        """
        try:
            # Collect CPU metrics
            cpu_percent, cpu_count = self._collect_cpu_metrics()
            
            # Collect memory metrics
            mem_used, mem_total, mem_percent = self._collect_memory_metrics()
            
            # Collect GPU metrics
            gpu_percent, gpu_mem_used, gpu_mem_total, gpu_temp = self._collect_gpu_metrics()
            
            # Collect disk metrics
            disk_used, disk_total, disk_percent = self._collect_disk_metrics()
            
            # Get model performance metrics
            model_metrics = self._get_model_metrics()
            
            # Get cache stats
            cache_hit_rate = self._get_cache_hit_rate()
            
            # Calculate uptime
            uptime = int(time.time() - _APP_START_TIME)

            # Collect static system info
            sys_platform, py_version, dj_version = self._collect_system_info()

            # Load average (Unix only)
            load_avg = self._collect_load_average()

            # Check database connectivity
            db_connected = self._check_database()

            return ModelHealthMetrics(
                # GPU
                gpu_usage_percent=gpu_percent,
                gpu_memory_used_mb=gpu_mem_used,
                gpu_memory_total_mb=gpu_mem_total,
                gpu_temperature_celsius=gpu_temp,
                # CPU
                cpu_usage_percent=cpu_percent,
                cpu_count=cpu_count,
                # Memory
                memory_used_mb=mem_used,
                memory_total_mb=mem_total,
                memory_usage_percent=mem_percent,
                # Disk
                disk_used_mb=disk_used,
                disk_total_mb=disk_total,
                disk_usage_percent=disk_percent,
                # Active Sessions
                active_sessions=self._active_sessions,
                # Cache
                cache_hit_rate=cache_hit_rate,
                cache_size_mb=self._cache_stats.get("size_mb", 0),
                cache_connected=True,
                # Model
                model_name=self.model_name,
                token_count_today=model_metrics["token_count_today"],
                token_count_total=model_metrics["token_count_total"],
                avg_processing_speed_ms=model_metrics["avg_processing_speed_ms"],
                requests_today=model_metrics["requests_today"],
                requests_total=model_metrics["requests_total"],
                # System
                uptime_seconds=uptime,
                last_model_reload=model_metrics.get("last_model_reload"),
                platform=sys_platform,
                python_version=py_version,
                django_version=dj_version,
                load_average=load_avg,
                database_connected=db_connected,
                collected_at=datetime.utcnow(),
            )
        except Exception as e:
            logger.error(f"Failed to collect metrics: {e}")
            raise MetricsCollectionError(f"Failed to collect system metrics: {e}")
    
    def _collect_disk_metrics(self) -> Tuple[float, float, float]:
        """
        Collect disk usage metrics.
        
        Returns:
            Tuple of (used_mb, total_mb, percent)
        """
        if self._psutil:
            try:
                disk = self._psutil.disk_usage('/')
                used_mb = disk.used / (1024 * 1024)
                total_mb = disk.total / (1024 * 1024)
                percent = disk.percent
                return used_mb, total_mb, percent
            except Exception as e:
                logger.warning(f"Failed to get disk metrics via psutil: {e}")
        
        # Fallback values
        return 0.0, 0.0, 0.0
    
    def _get_cache_hit_rate(self) -> float:
        """Calculate cache hit rate percentage."""
        total = self._cache_stats.get("hits", 0) + self._cache_stats.get("misses", 0)
        if total == 0:
            return 0.0
        return (self._cache_stats["hits"] / total) * 100
    
    def _collect_system_info(self) -> Tuple[str, str, str]:
        """Collect static system information: platform, Python version, Django version."""
        try:
            sys_platform = platform_lib.system() or sys.platform
        except Exception:
            sys_platform = sys.platform

        py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

        try:
            import django
            dj_version = django.__version__
        except Exception:
            dj_version = 'Unknown'

        return sys_platform, py_version, dj_version

    def _collect_load_average(self) -> Optional[float]:
        """Collect 1-minute load average (Unix only)."""
        try:
            if hasattr(os, 'getloadavg'):
                return round(os.getloadavg()[0], 2)
        except Exception:
            pass
        if self._psutil:
            try:
                return round(self._psutil.getloadavg()[0], 2)
            except Exception:
                pass
        return None

    def _check_database(self) -> bool:
        """Ping the primary database to confirm connectivity."""
        try:
            from django.db import connection
            connection.ensure_connection()
            return True
        except Exception:
            return False

    def update_active_sessions(self, count: int) -> None:
        """Update active session count."""
        self._active_sessions = count
    
    def record_cache_access(self, is_hit: bool, size_delta_mb: float = 0) -> None:
        """Record a cache access for statistics."""
        if is_hit:
            self._cache_stats["hits"] += 1
        else:
            self._cache_stats["misses"] += 1
        self._cache_stats["size_mb"] += size_delta_mb
    
    def _collect_cpu_metrics(self) -> Tuple[float, int]:
        """
        Collect CPU usage metrics.
        
        Returns:
            Tuple of (cpu_percent, cpu_count)
        """
        if self._psutil:
            try:
                cpu_percent = self._psutil.cpu_percent(interval=0.1)
                cpu_count = self._psutil.cpu_count(logical=True) or 1
                return cpu_percent, cpu_count
            except Exception as e:
                logger.warning(f"Failed to get CPU metrics via psutil: {e}")
        
        # Fallback values
        return 0.0, os.cpu_count() or 1
    
    def _collect_memory_metrics(self) -> Tuple[float, float, float]:
        """
        Collect memory usage metrics.
        
        Returns:
            Tuple of (used_mb, total_mb, percent)
        """
        if self._psutil:
            try:
                mem = self._psutil.virtual_memory()
                used_mb = mem.used / (1024 * 1024)
                total_mb = mem.total / (1024 * 1024)
                percent = mem.percent
                return used_mb, total_mb, percent
            except Exception as e:
                logger.warning(f"Failed to get memory metrics via psutil: {e}")
        
        # Fallback values
        return 0.0, 0.0, 0.0
    
    def _collect_gpu_metrics(self) -> Tuple[float, float, float, Optional[float]]:
        """
        Collect GPU metrics if available.
        
        Returns:
            Tuple of (gpu_percent, gpu_mem_used_mb, gpu_mem_total_mb, temperature)
        """
        if self._pynvml and self._gpu_handle:
            try:
                # GPU utilization
                util = self._pynvml.nvmlDeviceGetUtilizationRates(self._gpu_handle)
                gpu_percent = util.gpu
                
                # GPU memory
                mem_info = self._pynvml.nvmlDeviceGetMemoryInfo(self._gpu_handle)
                gpu_mem_used = mem_info.used / (1024 * 1024)
                gpu_mem_total = mem_info.total / (1024 * 1024)
                
                # GPU temperature
                try:
                    temp = self._pynvml.nvmlDeviceGetTemperature(
                        self._gpu_handle, 
                        self._pynvml.NVML_TEMPERATURE_GPU
                    )
                except Exception:
                    temp = None
                
                return gpu_percent, gpu_mem_used, gpu_mem_total, temp
            except Exception as e:
                logger.warning(f"Failed to get GPU metrics: {e}")
        
        # No GPU available or error
        return 0.0, 0.0, 0.0, None
    
    def _get_model_metrics(self) -> Dict[str, Any]:
        """
        Get model performance metrics from in-memory counters.
        
        Returns:
            Dict with model metrics
        """
        global _model_metrics
        
        # Reset daily counters if date changed
        today = datetime.utcnow().date()
        if _model_metrics["last_reset_date"] != today:
            _model_metrics["token_count_today"] = 0
            _model_metrics["requests_today"] = 0
            _model_metrics["last_reset_date"] = today
        
        # Calculate average processing speed
        processing_times = _model_metrics["processing_times_ms"]
        avg_speed = sum(processing_times) / len(processing_times) if processing_times else 0.0
        
        return {
            "token_count_today": _model_metrics["token_count_today"],
            "token_count_total": _model_metrics["token_count_total"],
            "requests_today": _model_metrics["requests_today"],
            "requests_total": _model_metrics["requests_total"],
            "avg_processing_speed_ms": round(avg_speed, 2),
            "last_model_reload": None,  # Would be set when model is reloaded
        }
    
    def record_model_inference(self, token_count: int, processing_time_ms: float) -> None:
        """
        Record a model inference for metrics tracking.
        
        Args:
            token_count: Number of tokens processed
            processing_time_ms: Time taken for inference in milliseconds
        """
        global _model_metrics
        
        # Reset daily counters if date changed
        today = datetime.utcnow().date()
        if _model_metrics["last_reset_date"] != today:
            _model_metrics["token_count_today"] = 0
            _model_metrics["requests_today"] = 0
            _model_metrics["last_reset_date"] = today
        
        # Update counters
        _model_metrics["token_count_today"] += token_count
        _model_metrics["token_count_total"] += token_count
        _model_metrics["requests_today"] += 1
        _model_metrics["requests_total"] += 1
        
        # Keep last 100 processing times for averaging
        _model_metrics["processing_times_ms"].append(processing_time_ms)
        if len(_model_metrics["processing_times_ms"]) > 100:
            _model_metrics["processing_times_ms"] = _model_metrics["processing_times_ms"][-100:]
    
    def get_gpu_info(self) -> Optional[Dict[str, Any]]:
        """
        Get detailed GPU information.
        
        Returns:
            Dict with GPU details or None if not available
        """
        if not self._pynvml or not self._gpu_handle:
            return None
        
        try:
            name = self._pynvml.nvmlDeviceGetName(self._gpu_handle)
            if isinstance(name, bytes):
                name = name.decode('utf-8')
            
            return {
                "name": name,
                "driver_version": self._pynvml.nvmlSystemGetDriverVersion(),
                "cuda_version": self._pynvml.nvmlSystemGetCudaDriverVersion_v2() / 1000,
            }
        except Exception as e:
            logger.warning(f"Failed to get GPU info: {e}")
            return None
    
    def __del__(self):
        """Cleanup NVML on destruction."""
        if self._pynvml:
            try:
                self._pynvml.nvmlShutdown()
            except Exception:
                pass


# Singleton instance
_collector_instance: Optional[SystemMetricsCollector] = None


def get_metrics_collector(model_name: str = "verif-ai-bert") -> SystemMetricsCollector:
    """
    Get the singleton metrics collector instance.
    
    Args:
        model_name: Name of the model (only used on first call)
        
    Returns:
        SystemMetricsCollector instance
    """
    global _collector_instance
    if _collector_instance is None:
        _collector_instance = SystemMetricsCollector(model_name)
    return _collector_instance


def record_inference(token_count: int, processing_time_ms: float) -> None:
    """
    Convenience function to record a model inference.
    
    Args:
        token_count: Number of tokens processed
        processing_time_ms: Time taken for inference
    """
    collector = get_metrics_collector()
    collector.record_model_inference(token_count, processing_time_ms)


def get_current_metrics() -> ModelHealthMetrics:
    """
    Convenience function to get current system metrics.
    
    Returns:
        ModelHealthMetrics with current system state
    """
    collector = get_metrics_collector()
    return collector.collect_metrics()
