from fastapi import APIRouter, Depends
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database import get_db
from app.models import User
from app.services.url_service import create_url, redirect


router = APIRouter()


class URLIn(BaseModel):
    url: HttpUrl

class URLOut(BaseModel):
    id: int
    short_code: str
    username: str | None

#create an error response model
class ErrorResponse(BaseModel):
    detail: str

#use the error response model created
@router.post(
    "/urls",
    response_model=URLOut,
    responses={
        409: {
            "model": ErrorResponse,
            "description": "URL already exists"
        }
    }
)
def create_short_url(
    url_data: URLIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    new_url = create_url(
        db=db,
        original_url=str(url_data.url),
        user_id=current_user.id
    )

    return {
        "id": new_url.id,
        "short_code": new_url.short_code,
        "username": current_user.username
    }

@router.get("/{short_code}")
def redirection(
        short_code: str,
        db: Session = Depends(get_db)
):
    return redirect(
        db=db,
        short_code=short_code
    )