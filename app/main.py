from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import inspect, text
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.database import Base, engine
from app.auth.security import ADMIN_PASSWORD, ADMIN_USERNAME
from app.repositories import user_repository
from app.database import SessionLocal
from app.rate_limit import limiter
from app.routers import auth, todos, users



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
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(users.router)
app.include_router(auth.router)
app.include_router(todos.router)


@app.get("/")
async def home():
    return {"message": "To-Do App is running"}
