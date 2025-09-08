from src.models.user import User
from src.core.security import get_password_hash

def build_user(username="alice", password="Passw0rd!"):
    return User(username=username, password_hash=get_password_hash(password))
