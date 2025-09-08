from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index, CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from src.db.base import Base

class UserBookEvent(Base):
    __tablename__ = "user_book_events"
    __table_args__ = (
        CheckConstraint("event in ('view','like','rate')", name="ck_user_book_events_event_allowed"),
        CheckConstraint("(rating is NULL) OR (rating BETWEEN 1 AND 5)", name="ck_user_book_events_rating_range"),
    )

    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False, index=True)
    book_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True)
    event = Column(String(20), nullable=False)
    rating = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    book = relationship("Book", backref="user_events")

Index("ix_user_book_event_user_book", UserBookEvent.username, UserBookEvent.book_id)
