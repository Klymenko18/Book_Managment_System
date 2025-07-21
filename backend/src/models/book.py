from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from src.db.base import Base

class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    genre = Column(String, nullable=False)
    published_year = Column(Integer, nullable=False)

   
    author_id = Column(Integer, ForeignKey("authors.id"), nullable=True)

    author = relationship("Author", back_populates="books")
