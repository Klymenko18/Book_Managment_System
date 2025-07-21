from sqlalchemy.orm import Session
from src.models.book import Book
from src.schemas.book import BookCreate, BookUpdate

def create_book(db: Session, book: BookCreate):
    db_book = Book(title=book.title, genre=book.genre, published_year=book.published_year, author_id=book.author_id)
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book

def get_books(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Book).offset(skip).limit(limit).all()

def get_book_by_id(db: Session, book_id: int):
    return db.query(Book).filter(Book.id == book_id).first()

def update_book(db: Session, book_id: int, book: BookUpdate):
    db_book = db.query(Book).filter(Book.id == book_id).first()
    if db_book:
        db_book.title = book.title
        db_book.genre = book.genre
        db_book.published_year = book.published_year
        db_book.author_id = book.author_id
        db.commit()
        db.refresh(db_book)
        return db_book
    return None

def delete_book(db: Session, book_id: int):
    db_book = db.query(Book).filter(Book.id == book_id).first()
    if db_book:
        db.delete(db_book)
        db.commit()
        return db_book
    return None

