"""
WHY THIS WAS CHOSEN:
We implement a simple, deterministic in-memory Fixed Window Counter to rate limit requests at the API layer.
This protects the backend from abuse and unnecessary downstream LLM and database costs.
By using a dictionary of (window_start_time, count) per IP address, we keep the logic lightweight,
highly performant, and easy to test, satisfying all PRD constraints.
"""

import math
import time
from typing import Dict, Tuple

from fastapi import HTTPException, Request, status

from src.config import settings


class RateLimiter:
    """
    In-memory Fixed Window Counter rate limiter.
    """

    def __init__(self) -> None:
        # Maps client IP to a tuple of (window_start_time, request_count)
        self.windows: Dict[str, Tuple[float, int]] = {}

    def __call__(self, request: Request) -> None:
        """
        FastAPI dependency callable that checks and updates the rate limit.

        Args:
            request: The incoming FastAPI request.

        Raises:
            HTTPException: 429 Too Many Requests if the rate limit is exceeded.
        """
        # Determine client identity using IP address
        client_ip = request.client.host if request.client else "unknown"

        now = time.time()
        limit = settings.RATE_LIMIT_REQUESTS
        window_size = settings.RATE_LIMIT_WINDOW_SECONDS

        if client_ip not in self.windows:
            # Initialize a new window
            self.windows[client_ip] = (now, 1)
            return

        start_time, count = self.windows[client_ip]

        # Check if the current window has expired
        if now - start_time >= window_size:
            # Reset window
            self.windows[client_ip] = (now, 1)
            return

        # If limit is exceeded, raise HTTP 429 with Retry-After header
        if count >= limit:
            time_remaining = int(math.ceil(start_time + window_size - now))
            time_remaining = max(1, time_remaining)  # Ensure it is at least 1 second

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too Many Requests. Please try again later.",
                headers={"Retry-After": str(time_remaining)},
            )

        # Otherwise, increment the counter for the current window
        self.windows[client_ip] = (start_time, count + 1)
