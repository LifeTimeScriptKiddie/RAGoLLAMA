from functools import wraps
from fastapi import HTTPException, Request
from typing import Dict
import time
from collections import defaultdict

class TokenBucket:
    def __init__(self, capacity: int, refill_rate: int):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.last_refill = time.time()
    
    def consume(self, tokens: int = 1) -> bool:
        now = time.time()
        # Refill tokens
        time_passed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + (time_passed * self.refill_rate))
        self.last_refill = now
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

# In-memory rate limiter (use Redis in production)
buckets: Dict[str, TokenBucket] = defaultdict(lambda: TokenBucket(100, 1))

def rate_limit(requests: int, window: int):
    """Rate limiting decorator."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request object
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if request:
                # Create bucket key (IP + user if available)
                client_ip = request.client.host
                bucket_key = f"{client_ip}"
                
                # Check rate limit
                bucket = buckets[bucket_key]
                if not bucket.consume():
                    raise HTTPException(
                        status_code=429,
                        detail="Rate limit exceeded",
                        headers={"Retry-After": str(window)}
                    )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator