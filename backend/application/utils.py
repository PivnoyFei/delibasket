import bcrypt


def hash_password(password: str) -> bytes:
    """Генерирует хэшированную версию предоставленного пароля."""
    return bcrypt.hashpw(bytes(password, "utf-8"), bcrypt.gensalt())
