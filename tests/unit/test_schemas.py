import pytest
from src.schemas.author import AuthorCreate
from src.schemas.book import BookUpdate

@pytest.mark.unit
def test_author_schema_minimal():
    a = AuthorCreate(name="A")
    assert a.name == "A"

@pytest.mark.unit
def test_book_update_optional_fields():
    u = BookUpdate(title="X")
    assert u.title == "X"
