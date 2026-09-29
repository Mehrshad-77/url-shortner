from fastapi import FastAPI

from app.api.routes.urls import router as url_router
from app.api.routes.users import router as user_router
from app.api.routes.auth import router as auth_router

app = FastAPI(
    title="URL Shortener",
    version="0.1.0",
)


@app.get("/")
def root():
    return {"message": "URL Shortener API"}


app.include_router(url_router)
app.include_router(user_router)
app.include_router(auth_router)