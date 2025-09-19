import hashlib
import json
import random
import sqlite3
from functools import wraps
import base64


# кодирование пароля
def encrypt(text):
    return base64.b64encode(text.encode()).decode()

# декодирование пароля
def decrypt(encrypted_text):
    if not encrypted_text:
        return "Нельзя расшифровать None или пустую строку"
    return base64.b64decode(encrypted_text.encode()).decode()

# хэширование пароля
def hash_password(password):
    """хэширование пароля"""
    return hashlib.sha256(password.encode()).hexdigest()