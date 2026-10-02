from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database import get_db
from app.models import User
from app.schemas import (
    ErrorResponse,
    URLInput,
    UserOut,
    UserURLOut,
)
from app.services.url_service import (
    delete_url,
    get_user_urls,
    update_url,
)
from app.services.user_service import create_user

router = APIRouter()

class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)

@router.post("/users", response_model=UserOut, status_code=201)
def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    new_user = create_user(
        db=db,
        username=user_data.username,
        password=user_data.password
    )

    return {
        "id": new_user.id,
        "username": new_user.username
    }

@router.get("/users/me",
        response_model=UserOut,
        responses={
        401: {
            "model": ErrorResponse,
            "description": "Authentication credentials are invalid",
        },
    },
)
def get_my_profile(
    current_user: User = Depends(get_current_user)
):
    return {
        "id": current_user.id,
        "username": current_user.username
    }

@router.get("/users/me/urls",
        response_model=list[UserURLOut],
        responses={
        401: {
            "model": ErrorResponse,
            "description": "Authentication credentials are invalid",
        },
    },
)
def get_my_urls(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_user_urls(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )

@router.delete(
    "/users/me/urls/{short_code}",
    status_code=204,
    response_model=None,
    responses={
        401: {
            "model": ErrorResponse,
            "description": "Authentication credentials are invalid",
        },
        404: {
            "model": ErrorResponse,
            "description": "URL not found",
        },
    },
)
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

@router.patch(
    "/users/me/urls/{short_code}",
    response_model=UserURLOut,
    responses={
        400: {
            "model": ErrorResponse,
            "description": "The new URL is the same as the current one",
        },
        401: {
            "model": ErrorResponse,
            "description": "Authentication credentials are invalid",
        },
        404: {
            "model": ErrorResponse,
            "description": "URL not found",
        },
        409: {
            "model": ErrorResponse,
            "description": "URL already exists",
        },
    },
)

def update_my_url(
    short_code: str,
    url_data: URLInput,
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