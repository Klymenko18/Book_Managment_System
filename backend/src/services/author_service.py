from sqlalchemy.orm import Session
from src.models.author import Author
from src.schemas.author import AuthorCreate, AuthorUpdate

def create_author(db: Session, author: AuthorCreate):
    db_author = Author(name=author.name, biography=author.biography)
    db.add(db_author)
    db.commit()
    db.refresh(db_author)
    return db_author

def get_authors(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Author).offset(skip).limit(limit).all()

def get_author_by_id(db: Session, author_id: int):
    return db.query(Author).filter(Author.id == author_id).first()

def update_author(db: Session, author_id: int, author: AuthorUpdate):
    db_author = db.query(Author).filter(Author.id == author_id).first()
    if db_author:
        db_author.name = author.name
        db_author.biography = author.biography
        db.commit()
        db.refresh(db_author)
        return db_author
    return None

def delete_author(db: Session, author_id: int):
    db_author = db.query(Author).filter(Author.id == author_id).first()
    if db_author:
        db.delete(db_author)
        db.commit()
        return db_author
    return None
