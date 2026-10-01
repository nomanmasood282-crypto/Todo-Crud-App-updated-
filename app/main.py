from contextlib import asynccontextmanager
import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.database import Base, engine
from app.auth.security import ADMIN_PASSWORD, ADMIN_USERNAME
from app.repositories import user_repository
from app.database import SessionLocal
from app.rate_limit import limiter
from app.routers import auth, todos, users
from app.middleware import request_logging_middleware

load_dotenv()
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        columns = await connection.run_sync(
            lambda sync_connection: {
                column["name"] for column in inspect(sync_connection).get_columns("users")
            }
        )
        if "role" not in columns:
            await connection.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR NOT NULL DEFAULT 'user'"))
    async with SessionLocal() as db:
        await user_repository.create_admin(
            db, ADMIN_USERNAME, "pakistan@example.com", ADMIN_PASSWORD
        )
    yield
    await engine.dispose()

app = FastAPI(title="To-Do App", lifespan=lifespan)
app.middleware("http")(request_logging_middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
        if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(users.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(todos.router, prefix="/api/v1")


@app.get("/")
async def home():
    return {"message": "To-Do App is running"}
