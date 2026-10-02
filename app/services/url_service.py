from nanoid import generate
from fastapi import HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models import URL


BASE62 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"


def generate_short_code(length: int = 7) -> str:
    return generate(BASE62, size=length)


def create_url(
    db: Session,
    original_url: str,
    user_id: int | None = None
):
    while True:
        short_code = generate_short_code()

        existing_url = (
            db.query(URL)
            .filter(URL.short_code == short_code)
            .first()
        )

        if existing_url is None:
            break

    new_url = URL(
        original_url = original_url,
        short_code = short_code,
        user_id = user_id
    )

    try:
        db.add(new_url)
        db.commit()
        db.refresh(new_url)
    except:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="URL already exists"
        )

    return new_url


def redirect(
    db: Session,
    short_code: str
):
    url = (
        db.query(URL)
        .filter(URL.short_code == short_code)
        .first()
    )

    if url is None:
        raise HTTPException(
            status_code=404,
            detail="URL not found"
        )

    return RedirectResponse(
        url=url.original_url,
        status_code=307
    )

def delete_url(
    db: Session,
    short_code: str,
    user_id: int
):
    url = (
        db.query(URL)
        .filter(
            URL.user_id == user_id,
            URL.short_code == short_code
        )
        .first()
    )

    if url is None:
        raise HTTPException(
            status_code=404,
            detail = "URL not found" 
        )

    db.delete(url)
    db.commit()

def update_url(
    db: Session,
    short_code: str,
    user_id: int,
    original_url: str
):
    url = (
        db.query(URL)
        .filter(
            URL.user_id == user_id,
            URL.short_code == short_code
        )
        .first()
    )

    if url is None:
        raise HTTPException(
            status_code=404,
            detail= "URL not found"
        )

    if url.original_url == original_url:
        raise HTTPException(
            status_code=400,
            detail="The new URL is the same as the current one"
        )

    if db.query(URL).filter(URL.original_url == original_url).first():
        raise HTTPException(
            status_code=409,
            detail="URL already exists"
        )

    url.original_url = original_url

    db.commit()
    db.refresh(url)
    
    return url