from typing import Optional, Literal
from pydantic import BaseModel, field_validator
from datetime import datetime

GENRES = ["Fiction", "Non-Fiction", "Science", "History", "Programming"]

class BookBase(BaseModel):
    title: str
    genre: Literal["Fiction", "Non-Fiction", "Science", "History", "Programming"]
    published_year: int
    author_name: Optional[str] = None

    @field_validator("title")
    def validate_title(cls, v):
        if not v.strip():
            raise ValueError("Title must be a non-empty string")
        return v

    @field_validator("author_name")
    def validate_author(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Author name must be a non-empty string if provided")
        return v

    @field_validator("published_year")
    def validate_year(cls, v):
        current_year = datetime.now().year
        if v < 1800 or v > current_year:
            raise ValueError(f"Published year must be between 1800 and {current_year}")
        return v


class BookCreate(BookBase):
    pass


class BookUpdate(BookBase):
    pass


class BookInDBBase(BaseModel):
    id: int
    title: str
    genre: str
    published_year: int
    author_name: Optional[str] = None

    class Config:
        from_attributes = True


class Book(BookInDBBase):
    pass


class BookResponse(BookInDBBase):
    pass
