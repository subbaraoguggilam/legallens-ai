"""Small in-memory sliding-window rate limiter (per client IP + bucket).

Suitable for a single-process deployment. For multiple replicas, back this with
Redis (same interface) or enforce limits at the reverse proxy.
"""
from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

from app.core.config import get_settings

_lock = threading.Lock()
_hits: dict[tuple[str, str], deque[float]] = defaultdict(deque)


def reset_rate_limits() -> None:
    with _lock:
        _hits.clear()


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def rate_limiter(bucket: str):
    """Dependency factory: limits are read from settings at request time."""

    def dependency(request: Request) -> None:
        s = get_settings()
        limit = {
            "auth": s.rate_limit_auth,
            "ask": s.rate_limit_ask,
            "upload": s.rate_limit_upload,
        }.get(bucket, s.rate_limit_default)
        window = s.rate_limit_window_seconds
        now = time.monotonic()
        key = (_client_ip(request), bucket)
        with _lock:
            q = _hits[key]
            while q and now - q[0] > window:
                q.popleft()
            if len(q) >= limit:
                retry = max(1, int(window - (now - q[0])))
                raise HTTPException(
                    status_code=429,
                    detail="Too many requests. Please wait and try again.",
                    headers={"Retry-After": str(retry)},
                )
            q.append(now)

    return dependency
