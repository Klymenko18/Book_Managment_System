from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from src.db.base import Base

class Author(Base):
    __tablename__ = "authors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    biography = Column(String, nullable=True)

  
    books = relationship("Book", back_populates="author")
