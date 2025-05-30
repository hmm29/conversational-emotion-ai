import time
import functools
import asyncio
from typing import Callable, Any, Dict, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def timing_decorator(func: Callable) -> Callable:
    """Decorator to measure function execution time"""
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        
        execution_time = end_time - start_time
        logger.info(f"{func.__name__} executed in {execution_time:.3f} seconds")
        
        # Record performance metrics
        if hasattr(performance_monitor, 'record_function_time'):
            performance_monitor.record_function_time(func.__name__, execution_time)
        
        return result
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        execution_time = end_time - start_time
        logger.info(f"{func.__name__} executed in {execution_time:.3f} seconds")
        
        # Record performance metrics
        if hasattr(performance_monitor, 'record_function_time'):
            performance_monitor.record_function_time(func.__name__, execution_time)
        
        return result
    
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper

class PerformanceMonitor:
    """Monitor system performance and resource usage"""
    
    def __init__(self):
        self.metrics = {
            'api_calls': 0,
            'total_response_time': 0.0,
            'errors': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'function_times': {},
            'memory_usage': [],
            'cpu_usage': [],
            'timestamps': []
        }
        self._last_memory_check = None
        self._last_cpu_check = None
    
    def record_api_call(self, response_time: float, success: bool = True):
        """Record API call metrics"""
        self.metrics['api_calls'] += 1
        self.metrics['total_response_time'] += response_time
        
        if not success:
            self.metrics['errors'] += 1
    
    def record_cache_access(self, hit: bool):
        """Record cache access metrics"""
        if hit:
            self.metrics['cache_hits'] += 1
        else:
            self.metrics['cache_misses'] += 1
    
    def record_function_time(self, function_name: str, execution_time: float):
        """Record function execution time metrics"""
        if function_name not in self.metrics['function_times']:
            self.metrics['function_times'][function_name] = {
                'count': 0,
                'total_time': 0.0,
                'max_time': 0.0,
                'min_time': float('inf')
            }
        
        stats = self.metrics['function_times'][function_name]
        stats['count'] += 1
        stats['total_time'] += execution_time
        stats['max_time'] = max(stats['max_time'], execution_time)
        stats['min_time'] = min(stats['min_time'], execution_time)
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        total_calls = self.metrics['api_calls']
        
        if total_calls == 0:
            return {'message': 'No performance data yet'}
        
        avg_response_time = self.metrics['total_response_time'] / total_calls
        error_rate = self.metrics['errors'] / total_calls
        cache_hit_rate = (self.metrics['cache_hits'] / 
                         (self.metrics['cache_hits'] + self.metrics['cache_misses'])) if (self.metrics['cache_hits'] + self.metrics['cache_misses']) > 0 else 0
        
        function_metrics = {}
        for func_name, stats in self.metrics['function_times'].items():
            avg_time = stats['total_time'] / stats['count']
            function_metrics[func_name] = {
                'average_time': round(avg_time, 3),
                'max_time': round(stats['max_time'], 3),
                'min_time': round(stats['min_time'], 3),
                'calls': stats['count']
            }
        
        return {
            'total_api_calls': total_calls,
            'average_response_time': round(avg_response_time, 3),
            'error_rate': round(error_rate * 100, 2),
            'cache_hit_rate': round(cache_hit_rate * 100, 2),
            'total_errors': self.metrics['errors'],
            'function_metrics': function_metrics,
            'timestamp': datetime.now().isoformat()
        }

# Global performance monitor instance
performance_monitor = PerformanceMonitor()
