import time
from collections import defaultdict
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


request_timestamps = defaultdict(list)

class RateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI, max_requests: int = 10, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        current_time = time.time()

        timestamps = request_timestamps[client_ip]
        request_timestamps[client_ip] = [
            timestamp for timestamp in timestamps
            if current_time - timestamp < self.window_seconds
        ]

        if len(request_timestamps[client_ip]) >= self.max_requests:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again later."}
            )

        request_timestamps[client_ip].append(current_time)
        return await call_next(request)
