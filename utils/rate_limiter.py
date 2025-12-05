# =============================================================================
# Clinical Guideline Research Assistant
# Copyright (c) 2024. MIT License. See LICENSE file for details.
# =============================================================================
"""Simple in-memory rate limiter (no Redis required).

Provides basic rate limiting for API endpoints.
"""
import time
from collections import defaultdict
from typing import Dict, Tuple, Optional
from functools import wraps


class RateLimiter:
    """Simple in-memory rate limiter using sliding window."""
    
    def __init__(
        self,
        requests_per_minute: int = 10,
        requests_per_hour: int = 100
    ):
        """Initialize rate limiter.
        
        Args:
            requests_per_minute: Max requests per minute per key
            requests_per_hour: Max requests per hour per key
        """
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        
        # Store: {key: [(timestamp, count), ...]}
        self._minute_windows: Dict[str, list] = defaultdict(list)
        self._hour_windows: Dict[str, list] = defaultdict(list)
    
    def _clean_old_entries(self, entries: list, window_seconds: int) -> list:
        """Remove entries older than window."""
        cutoff = time.time() - window_seconds
        return [e for e in entries if e[0] > cutoff]
    
    def _count_requests(self, entries: list) -> int:
        """Count total requests in entries."""
        return sum(e[1] for e in entries)
    
    def is_allowed(self, key: str = "global") -> Tuple[bool, Optional[str]]:
        """Check if request is allowed.
        
        Args:
            key: Rate limit key (e.g., API key, IP address)
            
        Returns:
            Tuple of (allowed: bool, error_message: Optional[str])
        """
        now = time.time()
        
        # Clean old entries
        self._minute_windows[key] = self._clean_old_entries(
            self._minute_windows[key], 60
        )
        self._hour_windows[key] = self._clean_old_entries(
            self._hour_windows[key], 3600
        )
        
        # Check minute limit
        minute_count = self._count_requests(self._minute_windows[key])
        if minute_count >= self.requests_per_minute:
            return False, f"Rate limit exceeded: {self.requests_per_minute}/minute"
        
        # Check hour limit
        hour_count = self._count_requests(self._hour_windows[key])
        if hour_count >= self.requests_per_hour:
            return False, f"Rate limit exceeded: {self.requests_per_hour}/hour"
        
        return True, None
    
    def record_request(self, key: str = "global"):
        """Record a request for rate limiting.
        
        Args:
            key: Rate limit key
        """
        now = time.time()
        self._minute_windows[key].append((now, 1))
        self._hour_windows[key].append((now, 1))
    
    def check_and_record(self, key: str = "global") -> Tuple[bool, Optional[str]]:
        """Check if allowed and record request if so.
        
        Args:
            key: Rate limit key
            
        Returns:
            Tuple of (allowed: bool, error_message: Optional[str])
        """
        allowed, error = self.is_allowed(key)
        if allowed:
            self.record_request(key)
        return allowed, error
    
    def get_remaining(self, key: str = "global") -> Dict[str, int]:
        """Get remaining requests for a key.
        
        Args:
            key: Rate limit key
            
        Returns:
            Dict with remaining counts for minute and hour windows
        """
        # Clean old entries first
        self._minute_windows[key] = self._clean_old_entries(
            self._minute_windows[key], 60
        )
        self._hour_windows[key] = self._clean_old_entries(
            self._hour_windows[key], 3600
        )
        
        minute_count = self._count_requests(self._minute_windows[key])
        hour_count = self._count_requests(self._hour_windows[key])
        
        return {
            "remaining_per_minute": max(0, self.requests_per_minute - minute_count),
            "remaining_per_hour": max(0, self.requests_per_hour - hour_count)
        }
    
    def reset(self, key: str = "global"):
        """Reset rate limits for a key.
        
        Args:
            key: Rate limit key to reset
        """
        self._minute_windows[key] = []
        self._hour_windows[key] = []


# Singleton instance
_rate_limiter = None

def get_rate_limiter() -> RateLimiter:
    """Get or create singleton rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(
            requests_per_minute=10,
            requests_per_hour=100
        )
    return _rate_limiter


def rate_limit(key_func=None):
    """Decorator to rate limit a function.
    
    Args:
        key_func: Function to extract rate limit key from args.
                  If None, uses "global" key.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            limiter = get_rate_limiter()
            
            # Get key
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                key = "global"
            
            # Check rate limit
            allowed, error = limiter.check_and_record(key)
            if not allowed:
                raise RateLimitExceeded(error)
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""
    pass


if __name__ == "__main__":
    # Quick test
    print("Testing rate limiter...")
    
    limiter = RateLimiter(requests_per_minute=5, requests_per_hour=20)
    
    # Make some requests
    for i in range(7):
        allowed, error = limiter.check_and_record("test_user")
        print(f"Request {i+1}: {'Allowed' if allowed else f'Blocked - {error}'}")
    
    print(f"\nRemaining: {limiter.get_remaining('test_user')}")
