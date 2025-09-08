from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories.author_repo import AuthorRepository
from src.models.author import Author

class AuthorService:
    def __init__(self, db: AsyncSession):
        self.repo = AuthorRepository(db)

    async def list(self, *, name: Optional[str], limit: int, offset: int, sort_by: str, sort_dir: str) -> Tuple[list[Author], int]:
        q = (name or "").strip() or None
        return await self.repo.list(name=q, limit=limit, offset=offset, sort_by=sort_by, sort_dir=sort_dir)

    async def get_or_404(self, author_id: int) -> Author:
        obj = await self.repo.get(author_id)
        if not obj:
            raise ValueError("not_found")
        return obj

    async def create(self, *, name: str, biography: Optional[str]) -> Author:
        name = name.strip()
        if not name:
            raise ValueError("bad_name")
        if await self.repo.get_by_name(name):
            raise ValueError("conflict")
        try:
            obj = await self.repo.create(name=name, biography=biography)
            await self.repo.save()
            return obj
        except Exception:
            await self.repo.rollback()
            raise

    async def update(self, *, author_id: int, name: str, biography: Optional[str]) -> Author:
        obj = await self.get_or_404(author_id)
        name = name.strip()
        if not name:
            raise ValueError("bad_name")
        other = await self.repo.get_by_name(name)
        if other and other.id != obj.id:
            raise ValueError("conflict")
        try:
            obj.name = name
            obj.biography = biography
            await self.repo.save()
            await self.repo.db.refresh(obj)
            return obj
        except Exception:
            await self.repo.rollback()
            raise

    async def delete(self, *, author_id: int) -> Author:
        obj = await self.get_or_404(author_id)
        try:
            await self.repo.delete(obj)
            await self.repo.save()
            return obj
        except Exception:
            await self.repo.rollback()
            raise
