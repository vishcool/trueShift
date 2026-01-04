"""
TrueShift - Rate Limiter Middleware

Token bucket rate limiting per user/IP.
"""

import time
from collections import defaultdict
from typing import Callable, Dict, Tuple

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using token bucket algorithm.
    Limits requests per user (authenticated) or IP (anonymous).
    """

    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        burst_size: int = 10,
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.refill_rate = requests_per_minute / 60.0  # tokens per second

        # Token buckets: key -> (tokens, last_refill_time)
        self._buckets: Dict[str, Tuple[float, float]] = defaultdict(
            lambda: (burst_size, time.time())
        )

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """
        Process request with rate limiting.
        """
        # Skip rate limiting for health checks
        if request.url.path.startswith("/health") or request.url.path.startswith("/api/v1/health"):
            return await call_next(request)

        # Get identifier (user ID or IP)
        identifier = self._get_identifier(request)

        # Check rate limit
        allowed, tokens_remaining, retry_after = self._check_rate_limit(identifier)

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded",
                    "retry_after": retry_after,
                },
                headers={
                    "Retry-After": str(int(retry_after)),
                    "X-RateLimit-Remaining": "0",
                },
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Remaining"] = str(int(tokens_remaining))
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)

        return response

    def _get_identifier(self, request: Request) -> str:
        """
        Get identifier for rate limiting.
        Uses user ID if authenticated, otherwise IP.
        """
        # Try to get user ID from auth header
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            # Use a hash of the token as identifier
            # In production, this would be the decoded user ID
            return f"user:{hash(auth_header)}"

        # Fall back to IP
        client_ip = request.client.host if request.client else "unknown"
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()

        return f"ip:{client_ip}"

    def _check_rate_limit(
        self,
        identifier: str,
    ) -> Tuple[bool, float, float]:
        """
        Check if request is allowed under rate limit.
        Returns: (allowed, tokens_remaining, retry_after)
        """
        now = time.time()
        tokens, last_refill = self._buckets[identifier]

        # Refill tokens
        time_passed = now - last_refill
        tokens = min(
            self.burst_size,
            tokens + time_passed * self.refill_rate,
        )

        if tokens >= 1:
            # Allow request
            self._buckets[identifier] = (tokens - 1, now)
            return True, tokens - 1, 0
        else:
            # Deny request
            retry_after = (1 - tokens) / self.refill_rate
            return False, 0, retry_after
