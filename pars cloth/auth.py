# auth.py
from config import ALLOWED_USERS

def check_access(user_id: int) -> bool:
    """Проверяет, есть ли у пользователя доступ к боту"""
    return user_id in ALLOWED_USERS