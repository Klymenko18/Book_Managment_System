from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Body, Query, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, field_validator, model_validator, Field
from sqlalchemy import select

from src.core.security import create_access_token, get_current_user, hash_password, verify_password
from src.db.session import get_session
from src.schemas.user import Token, UserCreate, UserResponse
from src.schemas.book import BookResponse
from src.models.user_book_event import UserBookEvent
from src.services.recommendations import recommend_for_user
from src.services.user_service import UserService
from src.models.book import Book

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/tokens")

def svc(db: AsyncSession = Depends(get_session)) -> UserService:
    return UserService(db)

@router.get("/users", response_model=List[UserResponse], response_model_exclude_none=True)
async def list_users(s: UserService = Depends(svc)):
    return await s.list()

@router.get("/users/{id}", response_model=UserResponse, response_model_exclude_none=True)
async def get_user_by_id(id: int, s: UserService = Depends(svc)):
    try:
        return await s.get_or_404(id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

@router.post("/auth/tokens", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_session)):
    from src.repositories.user_repo import UserRepository
    repo = UserRepository(db)
    db_user = await repo.get_by_username(form_data.username)
    if db_user is None or not verify_password(form_data.password, db_user.password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/users", response_model=UserResponse, response_model_exclude_none=True)
async def register_user(user: UserCreate, s: UserService = Depends(svc)):
    try:
        hashed = hash_password(user.password)
        return await s.register(username=user.username, password_hash=hashed)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already registered")
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to register user")

@router.patch("/users/{id}", response_model=UserResponse, response_model_exclude_none=True)
async def update_user(id: int, user_update: UserCreate, s: UserService = Depends(svc), current_user: dict = Depends(get_current_user)):
    try:
        hashed = hash_password(user_update.password)
        return await s.update(user_id=id, username=user_update.username, password_hash=hashed)
    except ValueError as e:
        if str(e) == "not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        if str(e) == "conflict":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already registered")
        raise
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update user")

@router.delete("/users/{id}", response_model=UserResponse, response_model_exclude_none=True)
async def delete_user(id: int, s: UserService = Depends(svc), current_user: dict = Depends(get_current_user)):
    try:
        return await s.delete(user_id=id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete user")

class UserEventIn(BaseModel):
    book_id: int
    event: str
    rating: Optional[int] = Field(None, ge=1, le=5)

    @field_validator("event")
    def _event_ok(cls, v: str) -> str:
        allowed = {"view", "like", "rate"}
        if v not in allowed:
            raise ValueError(f"event must be one of {allowed}")
        return v

    @model_validator(mode="after")
    def _rating_required_for_rate(self):
        if self.event == "rate" and self.rating is None:
            raise ValueError('rating must be 1..5 when event="rate"')
        return self

@router.post("/users/me/events", status_code=status.HTTP_204_NO_CONTENT)
async def add_user_event(payload: UserEventIn = Body(...), db: AsyncSession = Depends(get_session), current_user: dict = Depends(get_current_user)):
    username = current_user.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    if not (await db.execute(select(Book.id).where(Book.id == payload.book_id))).scalar():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    evt = UserBookEvent(username=username, book_id=payload.book_id, event=payload.event, rating=payload.rating)
    try:
        db.add(evt)
        await db.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to record event")

@router.get("/users/me/recommendations", response_model=List[BookResponse], response_model_exclude_none=True)
async def my_recommendations(limit: int = Query(10, ge=1, le=50), db: AsyncSession = Depends(get_session), current_user: dict = Depends(get_current_user)):
    username = current_user.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    rows = await recommend_for_user(db, username=username, limit=limit)
    return [
        BookResponse(
            id=b.id,
            title=b.title,
            genre=b.genre,
            published_year=b.published_year,
            author_name=b.author.name if b.author else None,
            isbn=b.isbn,
        )
        for b in rows
    ]
