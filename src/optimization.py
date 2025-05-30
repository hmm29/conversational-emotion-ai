import asyncio
import time
from functools import lru_cache, wraps
from typing import Dict, Any, List, Optional
import pickle
import hashlib
import logging
import psutil
import os
import statistics

logger = logging.getLogger(__name__)

class CacheManager:
    """Manage caching for API responses and computations"""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.cache = {}
        self.timestamps = {}
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
    
    def _is_expired(self, key: str) -> bool:
        """Check if cache entry is expired"""
        if key not in self.timestamps:
            return True
        return time.time() - self.timestamps[key] > self.ttl_seconds
    
    def _evict_expired(self):
        """Remove expired entries"""
        current_time = time.time()
        expired_keys = [
            key for key, timestamp in self.timestamps.items()
            if current_time - timestamp > self.ttl_seconds
        ]
        
        for key in expired_keys:
            self.cache.pop(key, None)
            self.timestamps.pop(key, None)
    
    def _evict_lru(self):
        """Evict least recently used items if cache is full"""
        if len(self.cache) >= self.max_size:
            # Remove oldest entry
            oldest_key = min(self.timestamps.keys(), key=lambda k: self.timestamps[k])
            self.cache.pop(oldest_key, None)
            self.timestamps.pop(oldest_key, None)
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        self._evict_expired()
        
        if key in self.cache and not self._is_expired(key):
            # Update timestamp for LRU
            self.timestamps[key] = time.time()
            return self.cache[key]
        
        return None
    
    def set(self, key: str, value: Any):
        """Set value in cache"""
        self._evict_expired()
        self._evict_lru()
        
        self.cache[key] = value
        self.timestamps[key] = time.time()
    
    def clear(self):
        """Clear all cache"""
        self.cache.clear()
        self.timestamps.clear()

# Global cache instance
cache_manager = CacheManager()

def cache_response(ttl_seconds: int = 3600):
    """Decorator to cache function responses"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            key_data = f"{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"
            cache_key = hashlib.md5(key_data.encode()).hexdigest()
            
            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result
            
            # Execute function and cache result
            logger.debug(f"Cache miss for {func.__name__}")
            result = await func(*args, **kwargs)
            cache_manager.set(cache_key, result)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            key_data = f"{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"
            cache_key = hashlib.md5(key_data.encode()).hexdigest()
            
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result
            
            logger.debug(f"Cache miss for {func.__name__}")
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result)
            
            return result
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

class BatchProcessor:
    """Process requests in batches for efficiency"""
    
    def __init__(self, batch_size: int = 10, max_wait_time: float = 1.0):
        self.batch_size = batch_size
        self.max_wait_time = max_wait_time
        self.pending_requests = []
        self.results = {}
        self.last_batch_time = time.time()
    
    async def add_request(self, request_id: str, request_data: Any) -> Any:
        """Add request to batch and wait for result"""
        self.pending_requests.append((request_id, request_data))
        
        # Process batch if conditions are met
        if (len(self.pending_requests) >= self.batch_size or 
            time.time() - self.last_batch_time >= self.max_wait_time):
            await self._process_batch()
        
        # Wait for result
        while request_id not in self.results:
            await asyncio.sleep(0.01)
        
        result = self.results.pop(request_id)
        return result
    
    async def _process_batch(self):
        """Process current batch of requests"""
        if not self.pending_requests:
            return
        
        batch = self.pending_requests.copy()
        self.pending_requests.clear()
        self.last_batch_time = time.time()
        
        # Process batch (override in subclasses)
        for request_id, request_data in batch:
            # Placeholder - implement actual batch processing
            self.results[request_id] = f"Processed: {request_data}"

class OptimizedConversationManager:
    """Optimized version with caching and batch processing"""
    
    def __init__(self, base_manager):
        self.base_manager = base_manager
        self.batch_processor = BatchProcessor()
    
    @cache_response(ttl_seconds=1800)  # Cache for 30 minutes
    async def get_similar_conversations(self, current_emotion: str, confidence: float) -> List[Dict]:
        """Get similar conversations for context (cached)"""
        # This would query a database or vector store for similar conversations
        # For demo, return empty list
        return []
    
    def optimize_conversation_history(self, max_history: int = 20):
        """Optimize conversation history by keeping only relevant parts"""
        if hasattr(self.base_manager, 'conversation_turns'):
            if len(self.base_manager.conversation_turns) > max_history:
                # Keep most recent and highest confidence turns
                turns = self.base_manager.conversation_turns
                
                # Sort by timestamp (most recent) and confidence
                sorted_turns = sorted(
                    turns, 
                    key=lambda x: (x.timestamp, x.emotion_result.confidence),
                    reverse=True
                )
                
                self.base_manager.conversation_turns = sorted_turns[:max_history]
    
    def precompute_personality_insights(self):
        """Precompute personality insights for faster access"""
        if not hasattr(self.base_manager, 'personality_profile'):
            return
        
        profile = self.base_manager.personality_profile
        
        # Cache computed insights
        insights = {
            'dominant_traits': sorted(
                profile.traits.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:3],
            'confidence_level': sum(profile.confidence.values()) / len(profile.confidence),
            'interaction_count': profile.update_count
        }
        
        cache_manager.set('personality_insights', insights)
        
        return insights

def optimize_streamlit_performance():
    """Apply Streamlit-specific optimizations"""
    import streamlit as st
    
    # Enable caching for expensive operations
    @st.cache_data(ttl=3600)  # Cache for 1 hour
    def load_visualization_data(conversation_history):
        """Cache visualization data preparation"""
        # Process conversation history for visualizations
        return {
            'emotion_timeline': [],
            'personality_data': {},
            'analytics_summary': {}
        }
    
    # Optimize session state
    if 'optimized_data' not in st.session_state:
        st.session_state.optimized_data = {}
    
    return load_visualization_data

class ResourceMonitor:
    """Monitor system resources and performance"""
    
    def __init__(self):
        self.metrics = {
            'memory_usage': [],
            'response_times': [],
            'api_calls': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
    
    def log_memory_usage(self):
        """Log current memory usage"""
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024
        self.metrics['memory_usage'].append(memory_mb)
        
        # Keep only last 100 measurements
        if len(self.metrics['memory_usage']) > 100:
            self.metrics['memory_usage'] = self.metrics['memory_usage'][-100:]
    
    def log_response_time(self, response_time: float):
        """Log API response time"""
        self.metrics['response_times'].append(response_time)
        
        # Keep only last 1000 measurements
        if len(self.metrics['response_times']) > 1000:
            self.metrics['response_times'] = self.metrics['response_times'][-1000:]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        if not self.metrics['response_times']:
            return {'message': 'No performance data available'}
        
        return {
            'avg_response_time': statistics.mean(self.metrics['response_times']),
            'p95_response_time': statistics.quantiles(self.metrics['response_times'], n=20)[18],
            'total_api_calls': self.metrics['api_calls'],
            'cache_hit_rate': (self.metrics['cache_hits'] / 
                             (self.metrics['cache_hits'] + self.metrics['cache_misses']) * 100) 
                             if (self.metrics['cache_hits'] + self.metrics['cache_misses']) > 0 else 0,
            'avg_memory_mb': statistics.mean(self.metrics['memory_usage']) if self.metrics['memory_usage'] else 0
        }

# Global performance monitor
performance_monitor = ResourceMonitor()
