from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from fastapi.security import OAuth2PasswordBearer

from src.db.session import get_db
from src.models.author import Author
from src.schemas.author import AuthorResponse, AuthorCreate, AuthorUpdate
from src.utils.token import verify_token

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")


def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        return verify_token(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )


@router.get("/retrieve/authors/", response_model=List[AuthorResponse])
async def get_authors(db: Session = Depends(get_db)):
    """
    Retrieve a list of all authors from the database.
    """
    try:
        authors = db.query(Author).all()
        return authors
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve authors"
        )


@router.get("/retrieve/authors/{author_id}", response_model=AuthorResponse)
async def get_author_by_id(author_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a specific author by their unique ID.
    """
    author = db.query(Author).filter(Author.id == author_id).first()
    if not author:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Author with ID {author_id} not found"
        )
    return author


@router.post("/create/authors/", response_model=AuthorResponse)
async def create_author(
    author: AuthorCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Create a new author with the given name and biography. Requires authentication.
    """
    existing_author = db.query(Author).filter(Author.name == author.name.strip()).first()
    if existing_author:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Author '{author.name}' already exists"
        )
    try:
        new_author = Author(name=author.name.strip(), biography=author.biography)
        db.add(new_author)
        db.commit()
        db.refresh(new_author)
        return new_author
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create author"
        )


@router.put("/update/authors/{author_id}/", response_model=AuthorResponse)
async def update_author(
    author_id: int,
    author_update: AuthorUpdate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Update an existing author's information by ID. Requires authentication.
    """
    author = db.query(Author).filter(Author.id == author_id).first()
    if not author:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Author with ID {author_id} not found"
        )
    try:
        author.name = author_update.name.strip()
        author.biography = author_update.biography
        db.commit()
        db.refresh(author)
        return author
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update author"
        )


@router.delete("/delete/authors/{author_id}/", response_model=AuthorResponse)
async def delete_author(
    author_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Delete an author from the database by ID. Requires authentication.
    """
    author = db.query(Author).filter(Author.id == author_id).first()
    if not author:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Author with ID {author_id} not found"
        )
    try:
        db.delete(author)
        db.commit()
        return author
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete author"
        )
