from sqlalchemy.orm import declarative_base
import importlib

Base = declarative_base()

def get_user():
    User = importlib.import_module('src.models.user').User
    return User

def get_book():
    Book = importlib.import_module('src.models.book').Book
    return Book

def get_author():
    Author = importlib.import_module('src.models.author').Author
    return Author

metadata = Base.metadata
