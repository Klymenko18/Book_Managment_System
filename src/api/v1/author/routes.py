from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.session import get_session
from src.core.security import get_current_user
from src.schemas.author import AuthorCreate, AuthorResponse, AuthorUpdate, PaginatedAuthors
from src.services.author_service import AuthorService

router = APIRouter()

def svc(db: AsyncSession = Depends(get_session)) -> AuthorService:
    return AuthorService(db)

@router.get("/authors", response_model=PaginatedAuthors, response_model_exclude_none=True)
async def list_authors(
    name: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: Optional[str] = Query("name", pattern="^(name|id)$"),
    sort_dir: Optional[str] = Query("asc", pattern="^(asc|desc)$"),
    s: AuthorService = Depends(svc),
):
    rows, total = await s.list(name=name, limit=limit, offset=offset, sort_by=sort_by or "name", sort_dir=sort_dir or "asc")
    items = [AuthorResponse.model_validate(a) for a in rows]
    next_offset = offset + limit if (offset + limit) < total else None
    return PaginatedAuthors(items=items, total=total, limit=limit, offset=offset, next_offset=next_offset)

@router.get("/authors/{id}", response_model=AuthorResponse, response_model_exclude_none=True)
async def get_author_by_id(id: int, s: AuthorService = Depends(svc)):
    try:
        return await s.get_or_404(id)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Author with ID {id} not found")

@router.post("/authors", response_model=AuthorResponse, response_model_exclude_none=True, status_code=status.HTTP_201_CREATED)
async def create_author(author: AuthorCreate, s: AuthorService = Depends(svc), current_user: dict = Depends(get_current_user)):
    try:
        return await s.create(name=author.name, biography=author.biography)
    except ValueError as e:
        if str(e) == "conflict":
            raise HTTPException(status_code=409, detail=f"Author '{author.name.strip()}' already exists")
        if str(e) == "bad_name":
            raise HTTPException(status_code=400, detail="Bad author name")
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to create author")

@router.patch("/authors/{id}", response_model=AuthorResponse, response_model_exclude_none=True)
async def update_author(id: int, author_update: AuthorUpdate, s: AuthorService = Depends(svc), current_user: dict = Depends(get_current_user)):
    try:
        return await s.update(author_id=id, name=author_update.name, biography=author_update.biography)
    except ValueError as e:
        if str(e) == "not_found":
            raise HTTPException(status_code=404, detail=f"Author with ID {id} not found")
        if str(e) == "conflict":
            raise HTTPException(status_code=409, detail=f"Author '{author_update.name.strip()}' already exists")
        if str(e) == "bad_name":
            raise HTTPException(status_code=400, detail="Bad author name")
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to update author")

@router.delete("/authors/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_author(
    id: int,
    s: AuthorService = Depends(svc),
    current_user: dict = Depends(get_current_user),
):
    try:
        await s.delete(author_id=id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Author with ID {id} not found")
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to delete author")