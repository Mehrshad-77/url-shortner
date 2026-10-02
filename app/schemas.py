from pydantic import BaseModel, HttpUrl


class ErrorResponse(BaseModel):
    detail: str


class UserOut(BaseModel):
    id: int
    username: str


class UserURLOut(BaseModel):
    id: int
    original_url: str
    short_code: str


class URLUpdate(BaseModel):
    url: HttpUrl

class URLInput(BaseModel):
    url: HttpUrl