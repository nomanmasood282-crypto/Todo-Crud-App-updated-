from fastapi import HTTPException
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession

from app import schemas
from app.auth.security import generate_acces_token, verify_password
from app.repositories import user_repository


async def register(user: schemas.UserCreate, db: AsyncSession):
    if await user_repository.get_by_username(user.username, db):
        raise HTTPException(status_code=400, detail="Username already exist")
    if await user_repository.get_by_email(user.email, db):
        raise HTTPException(status_code=400, detail="Email already exist")
    return await user_repository.create(user, db)


async def authenticate(username: str, password: str, db: AsyncSession):
    user = await user_repository.get_by_username(username, db)
    password_valid = (
        await run_in_threadpool(verify_password, password, user.hashed_password)
        if user
        else False
    )
    if not user or not password_valid:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return {"access_token": generate_acces_token({"sub": user.username}), "token_type": "bearer"}


async def get_all(db: AsyncSession):
    return await user_repository.get_all(db)


async def update_role(username: str, role: str, db: AsyncSession):
    if role not in {"user", "admin"}:
        raise HTTPException(status_code=400, detail="Role must be user or admin")
    user = await user_repository.update_role(username, role, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user