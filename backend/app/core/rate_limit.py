"""
Rate limiting middleware.
"""
from fastapi import Request, HTTPException, status
from functools import lru_cache
import time
from collections import defaultdict
from app.core.config import settings

# Simple in-memory rate limiter (use Redis for distributed systems)
_rate_limit_store = defaultdict(list)


def rate_limit(max_requests: int = 60, window_seconds: int = 60):
    """
    Rate limiting decorator.
    
    Args:
        max_requests: Maximum number of requests allowed
        window_seconds: Time window in seconds
    """
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            client_ip = request.client.host
            now = time.time()
            
            # Clean old entries
            _rate_limit_store[client_ip] = [
                timestamp for timestamp in _rate_limit_store[client_ip]
                if now - timestamp < window_seconds
            ]
            
            # Check rate limit
            if len(_rate_limit_store[client_ip]) >= max_requests:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded"
                )
            
            # Add current request
            _rate_limit_store[client_ip].append(now)
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator

