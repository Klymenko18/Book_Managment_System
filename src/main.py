from fastapi import FastAPI
from src.api.v1.author import routes as author_routes
from src.api.v1.book import routes as book_routes
from src.api.v1.user import routes as user_routes
from src.middlewares.rate_limiter import RateLimiterMiddleware

app = FastAPI()

app.add_middleware(
    RateLimiterMiddleware,
    max_requests=3,
    window_seconds=30,
    identify_by="ip_path",
    exclude_paths={"/docs", "/openapi.json", "/redoc"},
)

app.include_router(user_routes.router, prefix="/api/v1", tags=["users"])
app.include_router(author_routes.router, prefix="/api/v1", tags=["authors"])
app.include_router(book_routes.router, prefix="/api/v1", tags=["books"])

