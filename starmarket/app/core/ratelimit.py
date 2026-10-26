"""Small in-memory sliding-window limiter.

Single-process only. For several replicas move this to a shared store (e.g. Redis/DB).
"""
import time
from collections import defaultdict, deque

from fastapi import HTTPException


class RateLimiter:
    def __init__(self, limit: int, window_seconds: int):
        self.limit = limit
        self.window = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def hit(self, key: str) -> None:
        now = time.monotonic()
        q = self._hits[key]
        while q and now - q[0] > self.window:
            q.popleft()
        if len(q) >= self.limit:
            raise HTTPException(status_code=429, detail="Too many requests. Please wait and try again.")
        q.append(now)
        if len(self._hits) > 10000:  # keep memory bounded
            for k in [k for k, v in self._hits.items() if not v or now - v[-1] > self.window]:
                self._hits.pop(k, None)


auth_limiter = RateLimiter(limit=20, window_seconds=60)
order_limiter = RateLimiter(limit=10, window_seconds=60)
admin_limiter = RateLimiter(limit=120, window_seconds=60)
