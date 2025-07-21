from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session, joinedload
from fastapi.security import OAuth2PasswordBearer
from typing import List, Optional
from sqlalchemy import and_
from fastapi.responses import StreamingResponse

import csv
import io
import json

from src.db.session import get_db
from src.models.book import Book
from src.models.author import Author
from src.schemas.book import BookResponse, BookCreate, BookUpdate
from src.utils.token import verify_token

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        return verify_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

@router.get("/retrieve/books/", response_model=List[BookResponse])
async def get_books(db: Session = Depends(get_db)):
    """
    Retrieve a list of all books from the database.
    """
    try:
        books = db.query(Book).all()
        return books
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve books")

@router.get("/retrieve/books/{book_id}/", response_model=BookResponse)
async def get_book_by_id(book_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a specific book by its unique ID.
    """
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return book

@router.get("/filter/", response_model=List[BookResponse])
async def filter_books(
    title: Optional[str] = Query(None),
    author_name: Optional[str] = Query(None),
    genre: Optional[str] = Query(None),
    year_from: Optional[int] = Query(None, ge=1800),
    year_to: Optional[int] = Query(None, ge=1800),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1),
    db: Session = Depends(get_db)
):
    """
    Filter books by title, author, genre, and year range with pagination support.
    """
    try:
        query = db.query(Book).outerjoin(Book.author).options(joinedload(Book.author))
        filters = []

        if title:
            filters.append(Book.title.ilike(f"%{title}%"))
        if author_name:
            filters.append(Author.name.ilike(f"%{author_name}%"))
        if genre:
            filters.append(Book.genre == genre)
        if year_from is not None:
            filters.append(Book.published_year >= year_from)
        if year_to is not None:
            filters.append(Book.published_year <= year_to)

        books = query.filter(and_(*filters)).offset(skip).limit(limit).all()

        return [
            BookResponse(
                id=book.id,
                title=book.title,
                genre=book.genre,
                published_year=book.published_year,
                author_name=book.author.name if book.author else None
            ) for book in books
        ]
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to filter books")

@router.post("/create/books/", response_model=BookResponse)
async def create_book(
    book: BookCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Create a new book entry in the database. Requires authentication.
    """
    if not book.author_name or book.author_name.strip() == "":
        raise HTTPException(status_code=400, detail="Author name must be provided")

    try:
        author = db.query(Author).filter(Author.name == book.author_name.strip()).first()
        if not author:
            raise HTTPException(status_code=404, detail=f"Author '{book.author_name}' not found")

        existing = db.query(Book).filter(Book.title == book.title).first()
        if existing:
            raise HTTPException(status_code=409, detail="Book already exists")

        new_book = Book(
            title=book.title,
            genre=book.genre,
            published_year=book.published_year,
            author_id=author.id
        )

        db.add(new_book)
        db.commit()
        db.refresh(new_book)

        return BookResponse(
            id=new_book.id,
            title=new_book.title,
            genre=new_book.genre,
            published_year=new_book.published_year,
            author_name=author.name
        )
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create book")

@router.put("/update/books/{book_id}/", response_model=BookResponse)
async def update_book(
    book_id: int,
    book_update: BookUpdate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """
    Update an existing book entry by its ID. Requires authentication.
    """
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    if not book_update.author_name or book_update.author_name.strip() == "":
        raise HTTPException(status_code=400, detail="Author name must be provided")

    try:
        author = db.query(Author).filter(Author.name == book_update.author_name.strip()).first()
        if not author:
            raise HTTPException(status_code=404, detail=f"Author '{book_update.author_name}' not found")

        book.title = book_update.title
        book.genre = book_update.genre
        book.published_year = book_update.published_year
        book.author_id = author.id

        db.commit()
        db.refresh(book)

        return BookResponse(
            id=book.id,
            title=book.title,
            genre=book.genre,
            published_year=book.published_year,
            author_name=author.name
        )
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update book")

@router.delete("/delete/books/{book_id}/", response_model=BookResponse)
async def delete_book(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Delete a book entry from the database by its ID. Requires authentication.
    """
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    try:
        db.delete(book)
        db.commit()
        return BookResponse(
            id=book.id,
            title=book.title,
            genre=book.genre,
            published_year=book.published_year,
            author_name=book.author.name if book.author else None
        )
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete book")

@router.post("/import/", response_model=List[BookResponse])
def import_books(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Import books in bulk from a CSV or JSON file.
    """
    if file.content_type not in ["application/json", "text/csv"]:
        raise HTTPException(status_code=400, detail="File must be JSON or CSV")

    try:
        content = file.file.read()
        if file.filename.endswith(".json"):
            rows = json.loads(content)
        else:
            decoded = content.decode()
            reader = csv.DictReader(io.StringIO(decoded))
            rows = list(reader)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid file format: {str(e)}")

    created_books = []
    try:
        for row in rows:
            try:
                book_data = BookCreate(**row)
            except Exception:
                continue

            author = db.query(Author).filter_by(name=book_data.author_name.strip()).first()
            if not author:
                author = Author(name=book_data.author_name.strip())
                db.add(author)
                db.flush()

            book = Book(
                title=book_data.title,
                genre=book_data.genre,
                published_year=book_data.published_year,
                author_id=author.id
            )
            db.add(book)
            created_books.append(book)

        db.commit()

        return [
            BookResponse(
                id=book.id,
                title=book.title,
                genre=book.genre,
                published_year=book.published_year,
                author_name=book.author.name if book.author else None
            ) for book in created_books
        ]
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to import books")
