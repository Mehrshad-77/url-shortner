from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models import User
from app.security import hash_password, verify_password


def create_user(db: Session, username: str, password: str):
    existing_user = db.query(User).filter(User.username == username).first()

    if existing_user is not None:
        raise HTTPException(
            status_code=409,
            detail="Username already exists"
        )

    hashed_password = hash_password(password)

    new_user = User(
        username=username,
        hashed_password=hashed_password
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Username already exists"
        )

    return new_user

def authenticate_user(
        db: Session,
        username: str,
        password: str,
):
    user = (
        db.query(User)
        .filter(User.username == username)
        .first()
    )

    if user is None:
        return None

    if user.hashed_password is None:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user