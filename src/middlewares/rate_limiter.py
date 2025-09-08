from __future__ import annotations
import math, threading, time
from collections import defaultdict, deque
from typing import Deque, Dict, Iterable, Optional, Set
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

class RateLimiterMiddleware(BaseHTTPMiddleware):
    """Simple in-memory sliding-window limiter (single-process only)."""

    def __init__(
        self,
        app: ASGIApp,
        *,
        max_requests: int = 10,
        window_seconds: int = 60,
        identify_by: str = "ip_path",
        exclude_paths: Optional[Iterable[str]] = None,
        include_methods: Optional[Set[str]] = None,
    ) -> None:
        super().__init__(app)
        self.max_requests = int(max_requests)
        self.window_seconds = int(window_seconds)
        if identify_by not in {"ip", "ip_path"}:
            raise ValueError("identify_by must be 'ip' or 'ip_path'")
        self.identify_by = identify_by
        self.exclude_paths = set(exclude_paths or {"/docs", "/openapi.json", "/redoc", "/health", "/healthz"})
        self.include_methods = set(include_methods or {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD"})
        self._buckets: Dict[str, Deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def _identifier(self, request: Request) -> str:
        ip = request.client.host if request.client else "unknown"
        return ip if self.identify_by == "ip" else f"{ip}:{request.url.path}"

    def _cleanup(self, dq: Deque[float], now: float) -> None:
        win = self.window_seconds
        while dq and (now - dq[0]) >= win:
            dq.popleft()

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method == "OPTIONS" or request.url.path in self.exclude_paths:
            return await call_next(request)
        if request.method not in self.include_methods:
            return await call_next(request)

        now = time.time()
        ident = self._identifier(request)

        with self._lock:
            dq = self._buckets[ident]
            self._cleanup(dq, now)
            if len(dq) >= self.max_requests:
                oldest = dq[0]
                retry_after = max(0, int(math.ceil(self.window_seconds - (now - oldest))))
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded. Try again later."},
                    headers={
                        "Retry-After": str(retry_after),
                        "X-RateLimit-Limit": str(self.max_requests),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(now + retry_after)),
                    },
                )
            dq.append(now)
            remaining = self.max_requests - len(dq)
            oldest = dq[0]
            reset_in = max(0, int(math.ceil(self.window_seconds - (now - oldest))))

        response = await call_next(request)
        try:
            response.headers["X-RateLimit-Limit"] = str(self.max_requests)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(int(now + reset_in))
        except Exception:
            pass
        return response
