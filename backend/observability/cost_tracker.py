"""
Cost tracking and observability for external API calls.
"""
import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import threading

logger = logging.getLogger(__name__)

class CostTracker:
    """Track costs and performance of external API calls."""
    
    def __init__(self):
        self._lock = threading.Lock()
        self._call_counts: Dict[str, int] = {}
        self._total_costs: Dict[str, float] = {}
        self._total_duration: Dict[str, float] = {}
        self._start_times: Dict[str, float] = {}
        
    def start_call(self, call_id: str, service_name: str) -> None:
        """Start tracking a call."""
        with self._lock:
            self._start_times[call_id] = time.time()
            # Initialize counters if not present
            if service_name not in self._call_counts:
                self._call_counts[service_name] = 0
                self._total_costs[service_name] = 0.0
                self._total_duration[service_name] = 0.0
    
    def end_call(self, call_id: str, service_name: str, cost: float = 0.0) -> None:
        """End tracking a call and record metrics."""
        with self._lock:
            start_time = self._start_times.pop(call_id, None)
            if start_time is None:
                logger.warning(f"No start time found for call {call_id}")
                return
                
            duration = time.time() - start_time
            self._call_counts[service_name] += 1
            self._total_costs[service_name] += cost
            self._total_duration[service_name] += duration
            
            logger.debug(
                f"External call completed - Service: {service_name}, "
                f"Duration: {duration:.3f}s, Cost: ${cost:.4f}"
            )
    
    def get_stats(self, service_name: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics for a service or all services."""
        with self._lock:
            if service_name:
                if service_name not in self._call_counts:
                    return {}
                return {
                    "service": service_name,
                    "call_count": self._call_counts[service_name],
                    "total_cost": self._total_costs[service_name],
                    "total_duration": self._total_duration[service_name],
                    "avg_duration": (
                        self._total_duration[service_name] / self._call_counts[service_name]
                        if self._call_counts[service_name] > 0 else 0.0
                    ),
                    "avg_cost_per_call": (
                        self._total_costs[service_name] / self._call_counts[service_name]
                        if self._call_counts[service_name] > 0 else 0.0
                    )
                }
            else:
                # Return stats for all services
                stats = {}
                for service in self._call_counts:
                    stats[service] = {
                        "call_count": self._call_counts[service],
                        "total_cost": self._total_costs[service],
                        "total_duration": self._total_duration[service],
                        "avg_duration": (
                            self._total_duration[service] / self._call_counts[service]
                            if self._call_counts[service] > 0 else 0.0
                        ),
                        "avg_cost_per_call": (
                            self._total_costs[service] / self._call_counts[service]
                            if self._call_counts[service] > 0 else 0.0
                        )
                    }
                return stats
    
    def reset(self) -> None:
        """Reset all tracking data."""
        with self._lock:
            self._call_counts.clear()
            self._total_costs.clear()
            self._total_duration.clear()
            self._start_times.clear()

# Global cost tracker instance
cost_tracker = CostTracker()

def track_external_call(service_name: str, cost: float = 0.0):
    """Decorator to track external calls."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            call_id = f"{service_name}_{time.time()}_{id(func)}"
            cost_tracker.start_call(call_id, service_name)
            try:
                result = func(*args, **kwargs)
                cost_tracker.end_call(call_id, service_name, cost)
                return result
            except Exception as e:
                cost_tracker.end_call(call_id, service_name, cost)
                raise e
        return wrapper
    return decorator
