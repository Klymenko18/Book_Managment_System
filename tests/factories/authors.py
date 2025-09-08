from src.models.author import Author

def build_author(name="Franko", bio=None):
    return Author(name=name, bio=bio or "")
