from sqlalchemy.ext.asyncio import AsyncSession
from src.db.raw import fetch_all, fetch_one

BOOK_SORT_COLUMNS = {
    "title": "b.title",
    "created_at": "b.created_at",
    "updated_at": "b.updated_at",
    "isbn": "b.isbn",
}

def _sort_expr(sort_by: str | None, sort_dir: str | None) -> str:
    col = BOOK_SORT_COLUMNS.get((sort_by or "created_at"), "b.created_at")
    dir_sql = "DESC" if (sort_dir or "desc").lower() == "desc" else "ASC"
    return f"{col} {dir_sql}"

async def list_books_raw(session: AsyncSession, q: str | None, limit: int, offset: int, sort_by: str | None, sort_dir: str | None) -> dict:
    where = "WHERE 1=1"
    params: dict = {"limit": limit, "offset": offset}
    if q:
        where += " AND (b.title ILIKE :q OR COALESCE(a.name,'') ILIKE :q OR COALESCE(b.isbn,'') ILIKE :q)"
        params["q"] = f"%{q}%"

    order = _sort_expr(sort_by, sort_dir)

    sql_data = f"""
        SELECT b.id, b.title, b.isbn, b.created_at, b.updated_at,
               a.id AS author_id, a.name AS author_name
        FROM books b
        LEFT JOIN authors a ON a.id = b.author_id
        {where}
        ORDER BY {order}
        LIMIT :limit OFFSET :offset
    """

    sql_count = f"""
        SELECT COUNT(*)::int AS total
        FROM books b
        LEFT JOIN authors a ON a.id = b.author_id
        {where}
    """

    rows = await fetch_all(session, sql_data, params)
    total_row = await fetch_one(session, sql_count, params)
    return {"items": rows, "total": total_row["total"] if total_row else 0}
