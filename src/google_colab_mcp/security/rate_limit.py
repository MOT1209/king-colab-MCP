"""Simple thread-safe sliding-window rate limiter."""
from __future__ import annotations

import threading
import time
from collections import deque

from ..utils.errors import RateLimitError


class RateLimiter:
    def __init__(self, max_requests_per_minute: int):
        self.max_requests = max_requests_per_minute
        self._window_seconds = 60.0
        self._events: dict[str, deque] = {}
        self._lock = threading.Lock()

    def check(self, principal_id: str) -> None:
        if self.max_requests <= 0:
            return
        now = time.monotonic()
        with self._lock:
            events = self._events.setdefault(principal_id, deque())
            cutoff = now - self._window_seconds
            while events and events[0] < cutoff:
                events.popleft()
            if len(events) >= self.max_requests:
                raise RateLimitError(
                    f"Rate limit exceeded for '{principal_id}': "
                    f"{self.max_requests} requests / 60s.",
                )
            events.append(now)
