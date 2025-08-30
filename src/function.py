import base64
import hashlib

# кеширование
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# кодирование
def encrypt(text):
    return base64.b64encode(text.encode()).decode()

# декодирование
def decrypt(encrypted_text):
    if not encrypted_text:
        return "Нельзя расшифровать None или пустую строку"
    return base64.b64decode(encrypted_text.encode()).decode()