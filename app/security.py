from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from app.config import settings

password_Hash = PasswordHash.recommended()

def hash_password(password: str)-> str:
    return password_Hash.hash(password)

def verify_password(
        plain_password: str,
        hashed_password: str,
)-> bool:
    return password_Hash.verify(
        plain_password,
        hashed_password
    )

def create_access_token(
        data: dict,
        expires_minutes: int
)->str:
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes
    )

    to_encode.update({
        "exp": expire
    })

    return jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )