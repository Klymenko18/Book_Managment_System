from typing import Optional, List
from pydantic import BaseModel


class AuthorBase(BaseModel):
    name: str
    biography: Optional[str] = None


class AuthorCreate(AuthorBase):
    pass


class AuthorUpdate(AuthorBase):
    pass


class AuthorInDBBase(AuthorBase):
    id: int

    class Config:
        orm_mode = True


class Author(AuthorInDBBase):
    pass


class AuthorWithBooks(AuthorInDBBase):
    books: List['Book'] = []

class AuthorResponse(AuthorInDBBase):
    pass