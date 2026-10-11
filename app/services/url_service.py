from fastapi import HTTPException
from fastapi.responses import RedirectResponse
from nanoid import generate
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import URL

BASE62 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
MAX_SHORT_CODE_ATTEMPTS = 5
SHORT_CODE_CONSTRAINT = "urls_short_code_key"


def generate_short_code(length: int = 7) -> str:
    return generate(BASE62, size=length)


def get_url_by_short_code(db: Session, short_code: str) -> URL | None:
    return db.scalar(select(URL).where(URL.short_code == short_code))


def get_owned_url(db: Session, short_code: str, user_id: int) -> URL:
    url = db.scalar(
        select(URL).where(URL.user_id == user_id, URL.short_code == short_code)
    )

    if url is None:
        raise HTTPException(status_code=404, detail="URL not found")

    return url


def create_url(db: Session, original_url: str, user_id: int | None = None) -> URL:
    for _ in range(MAX_SHORT_CODE_ATTEMPTS):
        new_url = URL(
            original_url=original_url,
            short_code=generate_short_code(),
            user_id=user_id,
        )
        db.add(new_url)

        try:
            db.commit()
        except IntegrityError as e:
            db.rollback()

            if e.orig.diag.constraint_name == SHORT_CODE_CONSTRAINT:
                continue

            raise HTTPException(status_code=409, detail="URL already exists")

        db.refresh(new_url)
        return new_url

    raise HTTPException(status_code=500, detail="Could not generate a short code")


def redirect(db: Session, short_code: str) -> RedirectResponse:
    url = get_url_by_short_code(db, short_code)

    if url is None:
        raise HTTPException(status_code=404, detail="URL not found")

    return RedirectResponse(url=url.original_url, status_code=307)


def delete_url(db: Session, short_code: str, user_id: int) -> None:
    url = get_owned_url(db, short_code, user_id)

    db.delete(url)
    db.commit()


def update_url(
    db: Session,
    short_code: str,
    user_id: int,
    original_url: str,
) -> URL:
    url = get_owned_url(db, short_code, user_id)

    if url.original_url == original_url:
        raise HTTPException(
            status_code=400,
            detail="The new URL is the same as the current one",
        )

    url.original_url = original_url

    try:
        db.commit()
        db.refresh(url)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="URL already exists")

    return url


def get_user_urls(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 20,
) -> list[URL]:
    return list(
        db.scalars(
            select(URL)
            .where(URL.user_id == user_id)
            .order_by(URL.id)
            .offset(skip)
            .limit(limit)
        )
    )
