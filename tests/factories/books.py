from src.models.book import Book

def build_book(title="Foundation", genre="Science", published_year=1951, author_id=None):
    return Book(title=title, genre=genre, published_year=published_year, author_id=author_id)
