from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import User
from app.security import DUMMY_HASH, hash_password, verify_password


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.scalar(select(User).where(User.username == username.lower()))


def create_user(db: Session, username: str, password: str) -> User:
    if get_user_by_username(db, username) is not None:
        raise HTTPException(status_code=409, detail="Username already exists")

    new_user = User(
        username=username.lower(),
        hashed_password=hash_password(password),
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Username already exists")

    return new_user


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    user = get_user_by_username(db, username)

    # Always run a password check, even for unknown users, so response time
    # doesn't reveal which usernames exist.
    hashed = user.hashed_password if user else DUMMY_HASH
    password_ok = verify_password(password, hashed)

    return user if user and password_ok else None
