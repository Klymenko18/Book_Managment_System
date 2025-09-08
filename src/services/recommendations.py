from typing import List, Sequence, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, func, case, desc, select
from sqlalchemy.orm import selectinload
from src.models.book import Book
from src.models.user_book_event import UserBookEvent

async def recommend_for_book(db: AsyncSession, book_id: int, by: str = "hybrid", limit: int = 10) -> List[Book]:
    base = (await db.execute(select(Book).options(selectinload(Book.author)).where(Book.id == book_id))).scalars().first()
    if not base: return []
    recs: list[Book] = []
    if by in ("author","hybrid") and base.author_id is not None:
        q = (select(Book).options(selectinload(Book.author))
             .where(and_(Book.author_id==base.author_id, Book.id!=base.id))
             .order_by(Book.published_year.desc(), Book.title.asc()).limit(limit))
        recs.extend((await db.execute(q)).scalars().all())
    if by in ("genre","hybrid") and base.genre and len(recs)<limit:
        taken = {b.id for b in recs} | {base.id}
        q = (select(Book).options(selectinload(Book.author))
             .where(and_(Book.genre==base.genre, Book.id.not_in(taken)))
             .order_by(Book.published_year.desc(), Book.title.asc()).limit(limit-len(recs)))
        recs.extend((await db.execute(q)).scalars().all())
    return recs[:limit]

async def recommend_for_user(db: AsyncSession, username: str, limit: int = 10) -> List[Book]:
    w = (case((UserBookEvent.event=="like",3), else_=1) + case((UserBookEvent.event=="rate",2), else_=0))
    genre_scores: Sequence[tuple[str,int]] = (await db.execute(
        select(Book.genre, func.sum(w)).join(Book, Book.id==UserBookEvent.book_id)
        .where(UserBookEvent.username==username, Book.genre.isnot(None))
        .group_by(Book.genre).order_by(desc(func.sum(w))).limit(5)
    )).all()
    author_scores: Sequence[tuple[Optional[int],int]] = (await db.execute(
        select(Book.author_id, func.sum(w)).join(Book, Book.id==UserBookEvent.book_id)
        .where(UserBookEvent.username==username, Book.author_id.isnot(None))
        .group_by(Book.author_id).order_by(desc(func.sum(w))).limit(5)
    )).all()
    top_genres = [g for (g,_) in genre_scores]; top_author_ids = [a for (a,_) in author_scores]
    recs: list[Book] = []; taken: set[int] = set()
    if top_author_ids:
        q = (select(Book).options(selectinload(Book.author))
             .where(Book.author_id.in_(top_author_ids))
             .order_by(Book.published_year.desc(), Book.title.asc()).limit(limit))
        for b in (await db.execute(q)).scalars().all():
            if b.id not in taken:
                recs.append(b); taken.add(b.id)
                if len(recs)>=limit: return recs
    if top_genres and len(recs)<limit:
        q = (select(Book).options(selectinload(Book.author))
             .where(Book.genre.in_(top_genres), Book.id.not_in(taken))
             .order_by(Book.published_year.desc(), Book.title.asc()).limit(limit-len(recs)))
        recs.extend((await db.execute(q)).scalars().all())
    return recs[:limit]
