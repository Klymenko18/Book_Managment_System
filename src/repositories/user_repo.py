from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.user import User

class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list(self) -> List[User]:
        return (await self.db.execute(select(User))).scalars().all()

    async def get(self, user_id: int) -> Optional[User]:
        return await self.db.get(User, user_id)

    async def get_by_username(self, username: str) -> Optional[User]:
        return (await self.db.execute(select(User).where(User.username == username))).scalars().first()

    async def create(self, *, username: str, password_hash: str) -> User:
        obj = User(username=username, password=password_hash)
        self.db.add(obj)
        await self.db.flush()
        await self.db.refresh(obj)
        return obj

    async def update(self, obj: User, *, username: str, password_hash: str) -> User:
        obj.username = username
        obj.password = password_hash
        await self.db.flush()
        await self.db.refresh(obj)
        return obj

    async def delete(self, obj: User) -> None:
        await self.db.delete(obj)

    async def save(self) -> None:
        await self.db.commit()

    async def rollback(self) -> None:
        await self.db.rollback()
