from sqlalchemy.orm import declarative_base
import importlib

Base = declarative_base()

def get_user():
    return importlib.import_module('src.models.user').User

def get_book():
    return importlib.import_module('src.models.book').Book

def get_author():
    return importlib.import_module('src.models.author').Author

metadata = Base.metadata
