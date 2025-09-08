from typing import Any, Mapping
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

async def fetch_all(session: AsyncSession, sql: str, params: Mapping[str, Any] | None = None) -> list[dict]:
    res = await session.execute(text(sql), params or {})
    return [dict(row._mapping) for row in res.fetchall()]

async def fetch_one(session: AsyncSession, sql: str, params: Mapping[str, Any] | None = None) -> dict | None:
    res = await session.execute(text(sql), params or {})
    row = res.fetchone()
    return dict(row._mapping) if row else None

async def execute(session: AsyncSession, sql: str, params: Mapping[str, Any] | None = None) -> int:
    res = await session.execute(text(sql), params or {})
    await session.commit()
    return res.rowcount
