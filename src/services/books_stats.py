from sqlalchemy.ext.asyncio import AsyncSession
from src.db.raw import fetch_all, fetch_one

async def books_kpis(session: AsyncSession) -> dict:
    total = await fetch_one(session, "SELECT COUNT(*)::int AS total FROM books")
    by_author = await fetch_all(session, """
        SELECT a.name AS author, COUNT(b.id)::int AS books
        FROM authors a
        LEFT JOIN books b ON b.author_id = a.id
        GROUP BY a.name
        ORDER BY books DESC, author ASC
        LIMIT 50
    """)
    return {"total_books": total["total"] if total else 0, "by_author": by_author}
