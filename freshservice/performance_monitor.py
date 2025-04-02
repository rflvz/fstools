import time
from functools import wraps
import logging
from datetime import datetime

class PerformanceMonitor:
    def __init__(self):
        self.metrics = {}
        
    def timing_decorator(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            
            duration = end_time - start_time
            func_name = func.__name__
            
            if func_name not in self.metrics:
                self.metrics[func_name] = []
            
            self.metrics[func_name].append({
                'duration': duration,
                'timestamp': datetime.now(),
                'success': result is not None
            })
            
            return result
        return wrapper
        
    def get_statistics(self):
        stats = {}
        for func_name, calls in self.metrics.items():
            durations = [call['duration'] for call in calls]
            success_rate = sum(1 for call in calls if call['success']) / len(calls)
            
            stats[func_name] = {
                'avg_duration': sum(durations) / len(durations),
                'min_duration': min(durations),
                'max_duration': max(durations),
                'total_calls': len(calls),
                'success_rate': success_rate
            }
        
        return stats
