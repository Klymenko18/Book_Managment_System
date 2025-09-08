from typing import List, Optional
import os
import csv
import json
from io import StringIO
from uuid import uuid4

import aiofiles
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status, Response
from fastapi.responses import FileResponse
from pydantic import TypeAdapter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.db.session import get_session
from src.models.author import Author
from src.models.book import Book
from src.schemas.book import BookCreate, BookResponse, BookUpdate, PaginatedBooks
from src.schemas.imports import BookImportItem
from src.services.book_raw import list_books_raw
from src.services.book_service import BookService
from src.services.books_stats import books_kpis
from src.services.recommendations import recommend_for_book
from src.core.security import get_current_user 

router = APIRouter()


def svc(db: AsyncSession = Depends(get_session)) -> BookService:
    return BookService(db)


@router.get("/books/", response_model=PaginatedBooks, response_model_exclude_none=True)
async def list_books(
    title: Optional[str] = Query(None),
    author_name: Optional[str] = Query(None),
    genre: Optional[str] = Query(None),
    year_from: Optional[int] = Query(None, ge=1800),
    year_to: Optional[int] = Query(None, ge=1800),
    isbn: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: Optional[str] = Query("title", pattern=r"^(title|author|year|isbn)$"),
    sort_dir: Optional[str] = Query("asc", pattern=r"^(asc|desc)$"),
    s: BookService = Depends(svc),
):
    rows, total = await s.list(
        title=title,
        author_name=author_name,
        genre=genre,
        year_from=year_from,
        year_to=year_to,
        isbn=isbn,
        limit=limit,
        offset=offset,
        sort_by=sort_by or "title",
        sort_dir=sort_dir or "asc",
    )
    items = [
        BookResponse(
            id=b.id,
            title=b.title,
            genre=b.genre,
            published_year=b.published_year,
            author_name=b.author.name if b.author else None,
            isbn=b.isbn,
        )
        for b in rows
    ]
    next_offset = (offset + limit) if (offset + limit) < total else None
    return {"items": items, "total": total, "limit": limit, "offset": offset, "next_offset": next_offset}


@router.get("/books/{book_id}", response_model=BookResponse, response_model_exclude_none=True)
async def get_book_by_id(book_id: int, s: BookService = Depends(svc)):
    try:
        b = await s.get_or_404(book_id)
        return BookResponse(
            id=b.id,
            title=b.title,
            genre=b.genre,
            published_year=b.published_year,
            author_name=b.author.name if b.author else None,
            isbn=b.isbn,
        )
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")


@router.post("/books/", response_model=BookResponse, response_model_exclude_none=True, status_code=status.HTTP_201_CREATED)
async def create_book(
    book: BookCreate,
    s: BookService = Depends(svc),
    current_user: dict = Depends(get_current_user),  
):
    try:
        obj = await s.create(
            title=book.title,
            genre=book.genre,
            published_year=book.published_year,
            author_name=book.author_name or "",
            isbn=book.isbn,
        )
        return BookResponse(
            id=obj.id,
            title=obj.title,
            genre=obj.genre,
            published_year=obj.published_year,
            author_name=obj.author.name if obj.author else None,
            isbn=obj.isbn,
        )
    except ValueError as e:
        msg = str(e)
        if msg == "author_not_found":
            raise HTTPException(404, f"Author '{book.author_name}' not found")
        if msg == "isbn_conflict":
            raise HTTPException(409, "Book with this ISBN already exists")
        if msg == "conflict":
            raise HTTPException(409, "Book already exists for this author")
        if msg == "bad_author_name":
            raise HTTPException(400, "Author name must be provided")
        raise
    except Exception:
        raise HTTPException(500, "Failed to create book")


@router.patch("/books/{book_id}", response_model=BookResponse, response_model_exclude_none=True)
async def update_book(
    book_id: int,
    book_update: BookUpdate,
    s: BookService = Depends(svc),
    current_user: dict = Depends(get_current_user),  
):
    try:
        base = await s.get_or_404(book_id)
        obj = await s.update(
            book_id=book_id,
            title=book_update.title if (book_update.title is not None) else base.title,
            genre=book_update.genre if (book_update.genre is not None) else base.genre,
            published_year=book_update.published_year if (book_update.published_year is not None) else base.published_year,
            author_name=book_update.author_name,
            isbn=book_update.isbn if (book_update.isbn is not None) else None,
        )
        return BookResponse(
            id=obj.id,
            title=obj.title,
            genre=obj.genre,
            published_year=obj.published_year,
            author_name=obj.author.name if obj.author else None,
            isbn=obj.isbn,
        )
    except ValueError as e:
        msg = str(e)
        if msg == "not_found":
            raise HTTPException(404, "Book not found")
        if msg == "author_not_found":
            raise HTTPException(404, f"Author '{book_update.author_name}' not found")
        if msg == "isbn_conflict":
            raise HTTPException(409, "Another book with this ISBN already exists")
        if msg == "conflict":
            raise HTTPException(409, "Another book with this title & author already exists")
        if msg == "bad_author_name":
            raise HTTPException(400, "Author name must be provided")
        raise
    except Exception:
        raise HTTPException(500, "Failed to update book")


@router.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(
    book_id: int,
    s: BookService = Depends(svc),
    current_user: dict = Depends(get_current_user),  
):
    try:
        await s.delete(book_id=book_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except ValueError:
        raise HTTPException(404, "Book not found")
    except Exception:
        raise HTTPException(500, "Failed to delete book")


@router.post("/books/imports/", status_code=status.HTTP_201_CREATED)
async def import_books(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user),  
):
    os.makedirs(settings.IMPORT_DIR, exist_ok=True)
    ext = ".json" if file.filename.lower().endswith(".json") else ".csv"
    save_name = f"import_{uuid4().hex}{ext}"
    path = os.path.join(settings.IMPORT_DIR, save_name)

    content = await file.read()
    async with aiofiles.open(path, "wb") as f:
        await f.write(content)

    adapter = TypeAdapter(list[BookImportItem])
    items: list[BookImportItem] = []
    if ext == ".json":
        try:
            items = adapter.validate_json(content)
        except Exception:
            raise HTTPException(status_code=400, detail="JSON must be a list of books")
    else:
        rows = list(csv.DictReader(content.decode("utf-8").splitlines()))
        for r in rows:
            try:
                items.append(BookImportItem.model_validate(r))
            except Exception:
                continue

    created = 0
    for item in items:
        author = (await db.execute(select(Author).where(Author.name == item.author_name))).scalars().first()
        if not author:
            author = Author(name=item.author_name)
            db.add(author)
            await db.flush()

        exists = (
            await db.execute(select(Book).where(Book.title == item.title, Book.author_id == author.id))
        ).scalars().first()
        if exists:
            continue

        db.add(
            Book(
                title=item.title,
                genre=item.genre,
                published_year=item.published_year,
                author_id=author.id,
                isbn=item.isbn,
            )
        )
        created += 1

    await db.commit()
    return {"created": created, "stored_file": save_name}


@router.post("/books/exports/", status_code=status.HTTP_201_CREATED)
async def create_export(
    fmt: str = Query("csv", pattern=r"^(csv|json)$"),
    title: Optional[str] = Query(None),
    author_name: Optional[str] = Query(None),
    genre: Optional[str] = Query(None),
    year_from: Optional[int] = Query(None, ge=1800),
    year_to: Optional[int] = Query(None, ge=1800),
    sort_by: Optional[str] = Query("title", pattern=r"^(title|author|year|isbn)$"),
    sort_dir: Optional[str] = Query("asc", pattern=r"^(asc|desc)$"),
    s: BookService = Depends(svc),
    current_user: dict = Depends(get_current_user),  
):
    os.makedirs(settings.EXPORT_DIR, exist_ok=True)
    rows, _ = await s.list(
        title=title,
        author_name=author_name,
        genre=genre,
        year_from=year_from,
        year_to=year_to,
        isbn=None,
        limit=10_000,
        offset=0,
        sort_by=sort_by or "title",
        sort_dir=sort_dir or "asc",
    )
    fname = f"books_{uuid4().hex}.{fmt}"
    fullpath = os.path.join(settings.EXPORT_DIR, fname)

    if fmt == "csv":
        buf = StringIO(newline="")
        writer = csv.writer(buf, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["id", "title", "genre", "published_year", "author_name", "isbn"])
        for b in rows:
            writer.writerow(
                [
                    b.id,
                    b.title or "",
                    b.genre or "",
                    b.published_year or "",
                    b.author.name if b.author else "",
                    b.isbn or "",
                ]
            )
        async with aiofiles.open(fullpath, "w", encoding="utf-8", newline="") as f:
            await f.write(buf.getvalue())
    else:
        data = [
            {
                "id": b.id,
                "title": b.title,
                "genre": b.genre,
                "published_year": b.published_year,
                "author_name": b.author.name if b.author else None,
                "isbn": b.isbn,
            }
            for b in rows
        ]
        async with aiofiles.open(fullpath, "w", encoding="utf-8") as f:
            await f.write(json.dumps(data, ensure_ascii=False))

    return {"filename": fname}


@router.get("/books/exports/files/{filename}")
async def download_export(filename: str):
    fullpath = os.path.join(settings.EXPORT_DIR, filename)
    if not os.path.exists(fullpath):
        raise HTTPException(404, "File not found")
    media = "text/csv" if filename.endswith(".csv") else "application/json"
    return FileResponse(fullpath, media_type=media, filename=filename)


@router.get("/books/representations/raw/")
async def books_raw(
    q: str | None = Query(None),
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    sort_by: str | None = Query("created_at"),
    sort_dir: str | None = Query("desc"),
    session: AsyncSession = Depends(get_session),
):
    return await list_books_raw(session, q=q, limit=limit, offset=offset, sort_by=sort_by, sort_dir=sort_dir)


@router.get("/books/stats/")
async def books_stats_api(session: AsyncSession = Depends(get_session)):
    return await books_kpis(session)


@router.get("/books/{book_id}/recommendations", response_model=List[BookResponse], response_model_exclude_none=True)
async def recommend_books(
    book_id: int,
    by: str = Query("hybrid", pattern=r"^(author|genre|hybrid)$"),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_session),
):
    rows = await recommend_for_book(db, book_id, by=by, limit=limit)
    return [
        BookResponse(
            id=b.id,
            title=b.title,
            genre=b.genre,
            published_year=b.published_year,
            author_name=b.author.name if b.author else None,
            isbn=b.isbn,
        )
        for b in rows
    ]
