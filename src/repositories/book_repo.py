from __future__ import annotations

from typing import Optional, Tuple, List

import sqlalchemy as sa
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.book import Book
from src.models.author import Author


class BookRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        q: Optional[str] = None,
        title: Optional[str] = None,
        genre: Optional[str] = None,
        author_id: Optional[int] = None,
        author_name: Optional[str] = None,
        isbn: Optional[str] = None,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
    ) -> Tuple[List[Book], int]:
        filters = []
        join_author = author_name is not None

        if q:
            filters.append(Book.title.ilike(f"%{q}%"))
        if title:
            filters.append(Book.title == title)
        if genre:
            filters.append(Book.genre == genre)
        if author_id:
            filters.append(Book.author_id == author_id)
        if author_name:
            filters.append(Author.name == author_name)
        if isbn:
            filters.append(Book.isbn == isbn)
        if year_from is not None:
            filters.append(Book.published_year >= year_from)
        if year_to is not None:
            filters.append(Book.published_year <= year_to)

        base_select = select(Book)
        base_count = select(func.count()).select_from(Book)

        if join_author:
            base_select = base_select.join(Author)
            base_count = base_count.join(Author)

        stmt = (
            base_select.where(*filters)
            .order_by(Book.id.desc())
            .limit(limit)
            .offset(offset)
        )
        res = await self.db.execute(stmt)
        items = res.scalars().all()

        count_stmt = base_count.where(*filters)
        total_res = await self.db.execute(count_stmt)
        total = int(total_res.scalar() or 0)

        return items, total

    async def get(self, book_id: int) -> Optional[Book]:
        res = await self.db.execute(select(Book).where(Book.id == book_id))
        return res.scalars().first()

    async def create(
        self,
        *,
        title: str,
        genre: str,
        published_year: int,
        author_id: Optional[int],
        isbn: Optional[str] = None,
    ) -> Book:
        obj = Book(
            title=title,
            genre=genre,
            published_year=published_year,
            author_id=author_id,
            isbn=isbn,
        )
        self.db.add(obj)
        await self.db.flush()
        await self.db.refresh(obj)
        return obj

    async def update(
        self,
        obj: Book,
        *,
        title: str,
        genre: str,
        published_year: int,
        author_id: Optional[int],
        isbn: Optional[str] = None,
    ) -> Book:
        obj.title = title
        obj.genre = genre
        obj.published_year = published_year
        obj.author_id = author_id
        if isbn is not None:
            obj.isbn = isbn

        await self.db.flush()
        await self.db.refresh(obj)
        return obj

    async def delete(self, obj: Book) -> None:
        await self.db.delete(obj)

    async def save(self) -> None:
        await self.db.commit()

    async def rollback(self) -> None:
        await self.db.rollback()

    async def get_by_isbn(
        self, isbn: str, exclude_id: Optional[int] = None
    ) -> Optional[Book]:
        if not isbn:
            return None
        stmt = select(Book).where(Book.isbn == isbn)
        if exclude_id is not None:
            stmt = stmt.where(Book.id != exclude_id)
        res = await self.db.execute(stmt)
        return res.scalars().first()

    async def get_by_title_author(
        self,
        *,
        title: str,
        author_id: int,
        exclude_id: Optional[int] = None,
    ) -> Optional[Book]:
        stmt = select(Book).where(
            Book.author_id == author_id,
            func.lower(Book.title) == func.lower(sa.literal(title)),
        )
        if exclude_id is not None:
            stmt = stmt.where(Book.id != exclude_id)

        res = await self.db.execute(stmt)
        return res.scalars().first()
