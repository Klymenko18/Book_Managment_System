from typing import Optional, List
from pydantic import BaseModel, ConfigDict

class AuthorBase(BaseModel):
    name: str
    biography: Optional[str] = None

class AuthorCreate(AuthorBase):
    pass

class AuthorUpdate(AuthorBase):
    pass

class AuthorInDBBase(AuthorBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class Author(AuthorInDBBase):
    pass

class AuthorWithBooks(AuthorInDBBase):
    books: List["Book"] = []

class AuthorResponse(AuthorInDBBase):
    pass

class PaginatedAuthors(BaseModel):
    items: List[AuthorResponse]
    total: int
    limit: int
    offset: int
    next_offset: Optional[int] = None
