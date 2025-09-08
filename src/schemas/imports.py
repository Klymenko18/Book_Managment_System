from typing import Optional
from datetime import datetime
import re

from pydantic import BaseModel, Field, field_validator, ConfigDict
from src.schemas.book import Genre


def _normalize_isbn(v: Optional[str]) -> Optional[str]:
    if v is None:
        return None
    v = re.sub(r"[\s-]+", "", v).upper()
    if not v:
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


class BookImportItem(BaseModel):
    title: str = Field(min_length=1)
    author_name: str = Field(min_length=1)
    genre: Genre
    published_year: int
    isbn: Optional[str] = None

    model_config = ConfigDict(use_enum_values=True)

    @field_validator("title", "author_name")
    @classmethod
    def _not_empty(cls, v: str) -> str:
        v = (v or "").strip()
        if not v:
            raise ValueError("must not be empty")
        return v

    @field_validator("genre", mode="before")
    @classmethod
    def _genre_from_str(cls, v):
        if isinstance(v, Genre) or v is None:
            return v
        vs = str(v).strip()
        try:
            return Genre(vs)
        except ValueError:
            allowed = ", ".join(g.value for g in Genre)
            raise ValueError(f"genre must be one of: {allowed}")

    @field_validator("published_year")
    @classmethod
    def _year_ok(cls, v: int) -> int:
        cy = datetime.now().year
        if v < 1800 or v > cy:
            raise ValueError(f"published_year must be between 1800 and {cy}")
        return v

    @field_validator("isbn")
    @classmethod
    def _isbn_norm(cls, v: Optional[str]) -> Optional[str]:
        return _normalize_isbn(v)
