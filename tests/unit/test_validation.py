import pytest
from datetime import datetime
from src.schemas.book import BookCreate

@pytest.mark.unit
def test_book_create_validation_year_ok():
    current = datetime.utcnow().year
    obj = BookCreate(title="T", genre="Fiction", published_year=current, author_name="A")
    assert obj.published_year == current

@pytest.mark.unit
def test_book_create_validation_year_bad():
    with pytest.raises(Exception):
        BookCreate(title="T", genre="Fiction", published_year=1700, author_name="A")

@pytest.mark.unit
def test_book_create_validation_genre_bad():
    with pytest.raises(Exception):
        BookCreate(title="T", genre="UnknownGenre", published_year=2000, author_name="A")
