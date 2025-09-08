from __future__ import annotations

from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, field_validator, ConfigDict, Field
from datetime import datetime
import re


class Genre(str, Enum):
    fiction = "Fiction"
    nonfiction = "Non-Fiction"
    science = "Science"
    history = "History"
    programming = "Programming"


GENRES: list[str] = [g.value for g in Genre]


def _normalize_isbn(v: str | None) -> str | None:
    if v is None:
        return None
    v = re.sub(r"[\s-]+", "", v).upper()
    return v or None


class BookBase(BaseModel):
    title: Optional[str] = None
    genre: Optional[Genre] = None
    published_year: Optional[int] = None
    author_name: Optional[str] = None
    isbn: Optional[str] = None

    model_config = ConfigDict(use_enum_values=True)

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not v.strip():
            raise ValueError("Title must be a non-empty string")
        return v

    @field_validator("author_name")
    @classmethod
    def validate_author(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not v.strip():
            raise ValueError("Author name must be a non-empty string")
        return v

    @field_validator("published_year")
    @classmethod
    def validate_year(cls, v: Optional[int]) -> Optional[int]:
        if v is None:
            return v
        current_year = datetime.now().year
        if v < 1800 or v > current_year:
            raise ValueError(f"Published year must be between 1800 and {current_year}")
        return v

    @field_validator("isbn")
    @classmethod
    def validate_isbn(cls, v: Optional[str]) -> Optional[str]:
        v = _normalize_isbn(v)
        if v is None:
            return None
        if len(v) == 10:
            if not re.fullmatch(r"\d{9}[\dX]", v):
                raise ValueError("ISBN-10 must be 10 chars: 0-9 or last X")
        elif len(v) == 13:
            if not v.isdigit():
                raise ValueError("ISBN-13 must be 13 digits")
        else:
            raise ValueError("ISBN must be 10 or 13 characters long (ignoring dashes/spaces)")
        return v


class BookCreate(BookBase):
    title: str = Field(min_length=1)
    author_name: str = Field(min_length=1)
    genre: Genre
    published_year: int


class BookUpdate(BookBase):
    pass


class BookInDBBase(BaseModel):
    id: int
    title: str
    genre: Genre
    published_year: int
    author_name: Optional[str] = None
    isbn: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class Book(BookInDBBase):
    pass


class BookResponse(BookInDBBase):
    pass


class PaginatedBooks(BaseModel):
    items: List[BookResponse]
    total: int
    limit: int
    offset: int
    next_offset: Optional[int] = None


class BookEventIn(BaseModel):
    book_id: int
    event: str 
    rating: Optional[int] = Field(None, ge=1, le=5)
