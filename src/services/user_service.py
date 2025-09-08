from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories.user_repo import UserRepository
from src.models.user import User

class UserService:
    def __init__(self, db: AsyncSession):
        self.repo = UserRepository(db)

    async def list(self) -> list[User]:
        return await self.repo.list()

    async def get_or_404(self, user_id: int) -> User:
        obj = await self.repo.get(user_id)
        if not obj: raise ValueError("not_found")
        return obj

    async def register(self, *, username: str, password_hash: str) -> User:
        if await self.repo.get_by_username(username): raise ValueError("conflict")
        try:
            obj = await self.repo.create(username=username, password_hash=password_hash)
            await self.repo.save()
            return obj
        except Exception:
            await self.repo.rollback(); raise

    async def update(self, *, user_id: int, username: str, password_hash: str) -> User:
        obj = await self.get_or_404(user_id)
        other = await self.repo.get_by_username(username)
        if other and other.id != obj.id: raise ValueError("conflict")
        try:
            obj = await self.repo.update(obj, username=username, password_hash=password_hash)
            await self.repo.save()
            return obj
        except Exception:
            await self.repo.rollback(); raise

    async def delete(self, *, user_id: int) -> User:
        obj = await self.get_or_404(user_id)
        try:
            await self.repo.delete(obj)
            await self.repo.save()
            return obj
        except Exception:
            await self.repo.rollback(); raise
