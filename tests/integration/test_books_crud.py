from typing import List, Optional, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from src.models.book import Book
from src.models.author import Author

class BookRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list(
        self,
        *,
        title: Optional[str] = None,
        author_name: Optional[str] = None,
        genre: Optional[str] = None,
        isbn: Optional[str] = None,
        year_min: Optional[int] = None,
        year_max: Optional[int] = None,
        limit: int = 10,
        offset: int = 0,
        sort_by: str = "id",
        sort_dir: str = "asc",
    ) -> Tuple[List[Book], int]:
        stmt = select(Book).options(joinedload(Book.author))
        count_stmt = select(func.count(Book.id))

        if author_name is not None:
            stmt = stmt.join(Author)
            count_stmt = count_stmt.join(Author)

        conditions = []
        if title is not None:
            conditions.append(Book.title == title)
        if author_name is not None:
            conditions.append(Author.name == author_name)
        if genre is not None:
            conditions.append(Book.genre == genre)
        if isbn is not None:
            conditions.append(Book.isbn == isbn)
        if year_min is not None:
            conditions.append(Book.published_year >= year_min)
        if year_max is not None:
            conditions.append(Book.published_year <= year_max)

        if conditions:
            for c in conditions:
                stmt = stmt.where(c)
                count_stmt = count_stmt.where(c)

        sort_column = {
            "id": Book.id,
            "title": Book.title,
            "published_year": Book.published_year,
            "genre": Book.genre,
        }.get(sort_by, Book.id)

        stmt = stmt.order_by(sort_column.desc() if sort_dir == "desc" else sort_column.asc())
        stmt = stmt.limit(limit).offset(offset)

        total = (await self.db.execute(count_stmt)).scalar_one()
        rows = (await self.db.execute(stmt)).scalars().all()
        return rows, total
