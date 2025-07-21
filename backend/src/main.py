from fastapi import FastAPI
from src.api.user import routes as user_routes
from src.api.author import routes as author_routes
from src.api.book import routes as book_routes
from src.db.base import Base
from src.db.session import engine
from fastapi.security import OAuth2PasswordBearer
from src.middlewares.rate_limiter import RateLimiterMiddleware

app = FastAPI()


Base.metadata.create_all(bind=engine)
app.add_middleware(RateLimiterMiddleware)

app.include_router(user_routes.router, prefix="/api/v1", tags=["users"])
app.include_router(author_routes.router, prefix="/api/v1", tags=["authors"])
app.include_router(book_routes.router, prefix="/api/v1", tags=["books"])


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
