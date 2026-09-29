from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.user_service import create_user
from app.api.dependencies import get_current_user
from app.models import User, URL
from app.services.url_service import delete_url, update_url

router = APIRouter()

class UserCreate(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    id: int
    username: str

class UserURLOut(BaseModel):
    id: int
    original_url: str
    short_code: str

class URLUpdate(BaseModel):
    url: HttpUrl

@router.post("/users", response_model=UserOut, status_code=201)
def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    new_user = create_user(
        db=db,
        username= user_data.username,
        password= user_data.password
    )

    return{
        "id": new_user.id,
        "username": new_user.username
    }

@router.get("/users/me")
def get_my_profile(
    current_user: User = Depends(get_current_user)
):
    return{
        "id": current_user.id,
        "username": current_user.username
    }

@router.get("/users/me/urls", response_model=list[UserURLOut])
def get_my_urls(
     skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    urls = (
        db.query(URL)
        .filter(URL.user_id == current_user.id)
        .order_by(URL.id)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return urls

@router.delete("/users/me/urls/{short_code}", status_code=204)
def delete_my_url(
    short_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    delete_url(
        db=db,
        short_code=short_code,
        user_id=current_user.id
    )

@router.patch("/users/me/urls/{short_code}", response_model=UserURLOut)
def update_my_url(
    short_code: str,
    url_data: URLUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    updated_url = update_url(
        db=db,
        short_code=short_code,
        user_id=current_user.id,
        original_url=str(url_data.url)
    )

    return updated_url