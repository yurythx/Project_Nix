"""
Performance Monitoring and Optimization
Provides tools for monitoring and optimizing application performance
"""
import time
import logging
import psutil
import threading
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import wraps
from collections import defaultdict, deque
import json

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Performance metric data"""
    name: str
    value: float
    unit: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceProfile:
    """Performance profile for a function or operation"""
    name: str
    total_calls: int = 0
    total_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    avg_time: float = 0.0
    last_call: Optional[datetime] = None
    errors: int = 0


class IPerformanceMonitor(ABC):
    """Performance monitor interface"""
    
    @abstractmethod
    def start_timer(self, name: str) -> str:
        """Start timing an operation"""
        pass
    
    @abstractmethod
    def stop_timer(self, timer_id: str) -> float:
        """Stop timing an operation"""
        pass
    
    @abstractmethod
    def record_metric(self, name: str, value: float, unit: str = "ms", 
                     metadata: Optional[Dict[str, Any]] = None) -> None:
        """Record a performance metric"""
        pass
    
    @abstractmethod
    def get_profile(self, name: str) -> Optional[PerformanceProfile]:
        """Get performance profile for a name"""
        pass
    
    @abstractmethod
    def get_all_profiles(self) -> Dict[str, PerformanceProfile]:
        """Get all performance profiles"""
        pass


class PerformanceMonitor(IPerformanceMonitor):
    """Performance monitor implementation"""
    
    def __init__(self):
        self.timers: Dict[str, Dict[str, Any]] = {}
        self.profiles: Dict[str, PerformanceProfile] = {}
        self.metrics: List[PerformanceMetric] = []
        self._lock = threading.Lock()
    
    def start_timer(self, name: str) -> str:
        """Start timing an operation"""
        timer_id = f"{name}_{int(time.time() * 1000000)}"
        with self._lock:
            self.timers[timer_id] = {
                'name': name,
                'start_time': time.time(),
                'start_datetime': datetime.now()
            }
        return timer_id
    
    def stop_timer(self, timer_id: str) -> float:
        """Stop timing an operation"""
        with self._lock:
            if timer_id not in self.timers:
                logger.warning(f"Timer {timer_id} not found")
                return 0.0
            
            timer_data = self.timers[timer_id]
            elapsed_time = time.time() - timer_data['start_time']
            
            # Update profile
            name = timer_data['name']
            if name not in self.profiles:
                self.profiles[name] = PerformanceProfile(name=name)
            
            profile = self.profiles[name]
            profile.total_calls += 1
            profile.total_time += elapsed_time
            profile.min_time = min(profile.min_time, elapsed_time)
            profile.max_time = max(profile.max_time, elapsed_time)
            profile.avg_time = profile.total_time / profile.total_calls
            profile.last_call = datetime.now()
            
            # Record metric
            self.record_metric(name, elapsed_time * 1000, "ms")
            
            # Clean up timer
            del self.timers[timer_id]
            
            return elapsed_time
    
    def record_metric(self, name: str, value: float, unit: str = "ms", 
                     metadata: Optional[Dict[str, Any]] = None) -> None:
        """Record a performance metric"""
        metric = PerformanceMetric(
            name=name,
            value=value,
            unit=unit,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        
        with self._lock:
            self.metrics.append(metric)
            
            # Keep only last 1000 metrics
            if len(self.metrics) > 1000:
                self.metrics = self.metrics[-1000:]
    
    def get_profile(self, name: str) -> Optional[PerformanceProfile]:
        """Get performance profile for a name"""
        return self.profiles.get(name)
    
    def get_all_profiles(self) -> Dict[str, PerformanceProfile]:
        """Get all performance profiles"""
        return self.profiles.copy()
    
    def get_metrics(self, name: Optional[str] = None, 
                   since: Optional[datetime] = None) -> List[PerformanceMetric]:
        """Get metrics, optionally filtered by name and time"""
        with self._lock:
            metrics = self.metrics.copy()
        
        if name:
            metrics = [m for m in metrics if m.name == name]
        
        if since:
            metrics = [m for m in metrics if m.timestamp >= since]
        
        return metrics
    
    def clear_metrics(self) -> None:
        """Clear all metrics"""
        with self._lock:
            self.metrics.clear()
    
    def clear_profiles(self) -> None:
        """Clear all profiles"""
        with self._lock:
            self.profiles.clear()


class SystemMonitor:
    """System resource monitor"""
    
    def __init__(self):
        self.last_check = datetime.now()
        self.metrics_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
    
    def get_system_metrics(self) -> Dict[str, float]:
        """Get current system metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            metrics = {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_gb': memory.available / (1024**3),
                'memory_used_gb': memory.used / (1024**3),
                'disk_percent': disk.percent,
                'disk_free_gb': disk.free / (1024**3),
                'disk_used_gb': disk.used / (1024**3),
            }
            
            # Store in history
            timestamp = datetime.now()
            for key, value in metrics.items():
                self.metrics_history[key].append((timestamp, value))
            
            self.last_check = timestamp
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {}
    
    def get_metrics_history(self, metric_name: str, 
                           since: Optional[datetime] = None) -> List[tuple]:
        """Get metric history"""
        history = list(self.metrics_history[metric_name])
        
        if since:
            history = [(ts, val) for ts, val in history if ts >= since]
        
        return history
    
    def get_average_metric(self, metric_name: str, 
                          minutes: int = 5) -> Optional[float]:
        """Get average metric over time period"""
        since = datetime.now() - timedelta(minutes=minutes)
        history = self.get_metrics_history(metric_name, since)
        
        if not history:
            return None
        
        values = [val for _, val in history]
        return sum(values) / len(values)


# Global instances
performance_monitor = PerformanceMonitor()
system_monitor = SystemMonitor()


def monitor_performance(name: Optional[str] = None):
    """Decorator to monitor function performance"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            timer_name = name or f"{func.__module__}.{func.__name__}"
            timer_id = performance_monitor.start_timer(timer_name)
            
            try:
                result = func(*args, **kwargs)
                performance_monitor.stop_timer(timer_id)
                return result
            except Exception as e:
                # Record error in profile
                profile = performance_monitor.get_profile(timer_name)
                if profile:
                    profile.errors += 1
                performance_monitor.stop_timer(timer_id)
                raise
        
        return wrapper
    return decorator


def monitor_method_performance(name: Optional[str] = None):
    """Decorator to monitor method performance"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            timer_name = name or f"{type(self).__name__}.{func.__name__}"
            timer_id = performance_monitor.start_timer(timer_name)
            
            try:
                result = func(self, *args, **kwargs)
                performance_monitor.stop_timer(timer_id)
                return result
            except Exception as e:
                # Record error in profile
                profile = performance_monitor.get_profile(timer_name)
                if profile:
                    profile.errors += 1
                performance_monitor.stop_timer(timer_id)
                raise
        
        return wrapper
    return decorator


class PerformanceContext:
    """Context manager for performance monitoring"""
    
    def __init__(self, name: str):
        self.name = name
        self.timer_id = None
    
    def __enter__(self):
        self.timer_id = performance_monitor.start_timer(self.name)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.timer_id:
            performance_monitor.stop_timer(self.timer_id)


class QueryOptimizer:
    """Database query optimization utilities"""
    
    @staticmethod
    def optimize_queryset(queryset, select_related=None, prefetch_related=None):
        """Optimize queryset with select_related and prefetch_related"""
        if select_related:
            queryset = queryset.select_related(*select_related)
        if prefetch_related:
            queryset = queryset.prefetch_related(*prefetch_related)
        return queryset
    
    @staticmethod
    def only_fields(queryset, fields):
        """Optimize queryset to fetch only specific fields"""
        return queryset.only(*fields)
    
    @staticmethod
    def defer_fields(queryset, fields):
        """Optimize queryset to defer specific fields"""
        return queryset.defer(*fields)


class PerformanceReporter:
    """Generate performance reports"""
    
    @staticmethod
    def generate_profile_report() -> Dict[str, Any]:
        """Generate performance profile report"""
        profiles = performance_monitor.get_all_profiles()
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_operations': len(profiles),
            'profiles': {}
        }
        
        for name, profile in profiles.items():
            report['profiles'][name] = {
                'total_calls': profile.total_calls,
                'total_time': profile.total_time,
                'avg_time': profile.avg_time,
                'min_time': profile.min_time,
                'max_time': profile.max_time,
                'errors': profile.errors,
                'last_call': profile.last_call.isoformat() if profile.last_call else None
            }
        
        return report
    
    @staticmethod
    def generate_system_report() -> Dict[str, Any]:
        """Generate system performance report"""
        current_metrics = system_monitor.get_system_metrics()
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'current_metrics': current_metrics,
            'averages': {}
        }
        
        # Calculate averages for last 5 minutes
        for metric_name in current_metrics.keys():
            avg = system_monitor.get_average_metric(metric_name, minutes=5)
            if avg is not None:
                report['averages'][f"{metric_name}_5min_avg"] = avg
        
        return report
    
    @staticmethod
    def save_report_to_file(report: Dict[str, Any], filename: str) -> None:
        """Save performance report to file"""
        try:
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            logger.info(f"Performance report saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving performance report: {e}")


# Convenience functions
def start_performance_timer(name: str) -> str:
    """Start a performance timer"""
    return performance_monitor.start_timer(name)


def stop_performance_timer(timer_id: str) -> float:
    """Stop a performance timer"""
    return performance_monitor.stop_timer(timer_id)


def record_performance_metric(name: str, value: float, unit: str = "ms", 
                            metadata: Optional[Dict[str, Any]] = None) -> None:
    """Record a performance metric"""
    performance_monitor.record_metric(name, value, unit, metadata)


def get_performance_profile(name: str) -> Optional[PerformanceProfile]:
    """Get performance profile"""
    return performance_monitor.get_profile(name)


def get_system_metrics() -> Dict[str, float]:
    """Get current system metrics"""
    return system_monitor.get_system_metrics() 