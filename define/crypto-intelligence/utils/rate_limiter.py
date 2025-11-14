"""Rate limiter utility for API calls."""
import asyncio
import time


class RateLimiter:
    """Token bucket rate limiter."""
    
    def __init__(self, max_requests: int, time_window: int):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests allowed
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
        self.lock = asyncio.Lock()
    
    async def acquire(self):
        """Acquire permission to make request (blocks if rate limit reached)."""
        async with self.lock:
            now = time.time()
            # Remove old requests outside time window
            self.requests = [req_time for req_time in self.requests 
                           if now - req_time < self.time_window]
            
            if len(self.requests) >= self.max_requests:
                # Calculate wait time
                oldest = self.requests[0]
                wait_time = self.time_window - (now - oldest) + 0.1
                await asyncio.sleep(wait_time)
                # Refresh after waiting
                now = time.time()
                self.requests = [req_time for req_time in self.requests 
                               if now - req_time < self.time_window]
            
            self.requests.append(time.time())
