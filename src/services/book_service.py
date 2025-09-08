from typing import Optional, Tuple, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.repositories.book_repo import BookRepository
from src.models.book import Book
from src.models.author import Author

class BookService:
    def __init__(self, db: AsyncSession):
        self.repo = BookRepository(db)
        self.db = db

    async def list(self, **kwargs) -> Tuple[List[Book], int]:
        return await self.repo.list(**kwargs)

    async def get_or_404(self, book_id: int) -> Book:
        obj = await self.repo.get(book_id)
        if not obj: raise ValueError("not_found")
        return obj

    async def _author_by_name(self, name: str) -> Optional[Author]:
        return (await self.db.execute(select(Author).where(Author.name == name))).scalars().first()

    async def create(self, *, title: str, genre: str, published_year: int, author_name: str, isbn: Optional[str]) -> Book:
        author = await self._author_by_name(author_name.strip())
        if not author: raise ValueError("author_not_found")
        if isbn and await self.repo.get_by_isbn(isbn): raise ValueError("isbn_conflict")
        if await self.repo.get_by_title_author(title=title, author_id=author.id): raise ValueError("conflict")
        try:
            obj = await self.repo.create(title=title, genre=genre, published_year=published_year, author_id=author.id, isbn=isbn)
            await self.repo.save()
            return obj
        except Exception:
            await self.repo.rollback(); raise

    async def update(self, *, book_id: int, title: str, genre: str, published_year: int, author_name: Optional[str], isbn: Optional[str] = None) -> Book:
        obj = await self.get_or_404(book_id)
        if author_name is not None:
            if not author_name.strip(): raise ValueError("bad_author_name")
            author = await self._author_by_name(author_name.strip())
            if not author: raise ValueError("author_not_found")
            new_author_id = author.id
        else:
            new_author_id = obj.author_id

        if isbn is not None:
            if isbn and await self.repo.get_by_isbn(isbn, exclude_id=obj.id): raise ValueError("isbn_conflict")

        if (title != obj.title) or (new_author_id != obj.author_id):
            if await self.repo.get_by_title_author(title=title, author_id=new_author_id, exclude_id=obj.id):
                raise ValueError("conflict")

        try:
            obj = await self.repo.update(obj, title=title, genre=genre, published_year=published_year, author_id=new_author_id, isbn=isbn)
            await self.repo.save()
            return obj
        except Exception:
            await self.repo.rollback(); raise

    async def delete(self, *, book_id: int) -> None:
        obj = await self.get_or_404(book_id)
        try:
            await self.repo.delete(obj)
            await self.repo.save()
        except Exception:
            await self.repo.rollback(); raise
