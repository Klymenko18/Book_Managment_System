import asyncio
import pathlib
import pytest
from typing import AsyncGenerator
import httpx
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import select

from src.main import app
from src.db.base import Base
from src.db.session import get_session
from src.core.security import hash_password
from src.models.user import User

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def test_db_url():
    return "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="session")
async def engine(test_db_url):
    eng = create_async_engine(
        test_db_url,
        future=True,
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()

@pytest.fixture()
async def session(engine) -> AsyncGenerator[AsyncSession, None]:
    async_session = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)
    async with async_session() as s:
        yield s
        await s.rollback()

@pytest.fixture(autouse=True, scope="function")
def override_db_dep(session, monkeypatch):
    async def _get_session_override():
        yield session
    app.dependency_overrides[get_session] = _get_session_override
    yield
    app.dependency_overrides.pop(get_session, None)

@pytest.fixture(autouse=True)
def patch_rate_limiter(monkeypatch):
    try:
        from src.middlewares import rate_limiter
        if hasattr(rate_limiter, "get_rate_redis"):
            monkeypatch.setattr(rate_limiter, "get_rate_redis", lambda: None)
        if hasattr(rate_limiter, "close_rate_redis"):
            monkeypatch.setattr(rate_limiter, "close_rate_redis", lambda: None)
    except ImportError:
        pass
    app.user_middleware = [m for m in app.user_middleware if m.cls.__name__ != "RateLimiterMiddleware"]
    app.middleware_stack = app.build_middleware_stack()

@pytest.fixture()
async def client():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

@pytest.fixture(scope="session")
def data_dir() -> pathlib.Path:
    return pathlib.Path(__file__).parent / "data"

@pytest.fixture()
async def auth_user(session: AsyncSession):
    result = await session.execute(select(User).where(User.username == "tester"))
    user = result.scalars().first()
    if not user:
        user = User(username="tester")
        pw = hash_password("secret123")
        setattr(user, "password", pw)
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user

@pytest.fixture()
async def auth_headers(client, auth_user):
    r = await client.post(
        "/api/v1/auth/tokens",
        data={"username": "tester", "password": "secret123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 200, r.text
    token = r.json().get("access_token") or r.json().get("token")
    assert token
    return {"Authorization": f"Bearer {token}"}
