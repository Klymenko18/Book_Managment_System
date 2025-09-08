from typing import Optional, Sequence, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.author import Author

class AuthorRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list(self, *, name: Optional[str], limit: int, offset: int, sort_by: str, sort_dir: str) -> Tuple[list[Author], int]:
        stmt = select(Author)
        count_stmt = select(func.count(Author.id))
        if name:
            like = f"%{name}%"
            stmt = stmt.where(Author.name.ilike(like))
            count_stmt = count_stmt.where(Author.name.ilike(like))
        sort_map = {"name": Author.name, "id": Author.id}
        order_col = sort_map.get(sort_by, Author.name)
        order_col = order_col.desc() if sort_dir == "desc" else order_col.asc()
        total = int((await self.db.execute(count_stmt)).scalar() or 0)
        rows: Sequence[Author] = (await self.db.execute(stmt.order_by(order_col).offset(offset).limit(limit))).scalars().all()
        return list(rows), total

    async def get(self, author_id: int) -> Optional[Author]:
        return await self.db.get(Author, author_id)

    async def get_by_name(self, name: str) -> Optional[Author]:
        res = await self.db.execute(select(Author).where(Author.name == name))
        return res.scalar_one_or_none()

    async def create(self, *, name: str, biography: Optional[str]) -> Author:
        obj = Author(name=name, biography=biography)
        self.db.add(obj)
        await self.db.flush()
        await self.db.refresh(obj)
        return obj

    async def delete(self, author: Author) -> None:
        await self.db.delete(author)

    async def save(self) -> None:
        await self.db.commit()

    async def rollback(self) -> None:
        await self.db.rollback()
