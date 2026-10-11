from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class ErrorResponse(BaseModel):
    detail: str


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str


class URLInput(BaseModel):
    url: HttpUrl


class URLOut(BaseModel):
    id: int
    short_code: str
    username: str


class UserURLOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    original_url: str
    short_code: str
