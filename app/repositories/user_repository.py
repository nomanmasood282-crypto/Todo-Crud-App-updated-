from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.auth import hash_password
from fastapi.concurrency import run_in_threadpool


async def get_by_username(username: str, db: AsyncSession):
    result = await db.execute(select(models.User).where(models.User.username == username))
    return result.scalars().first()


async def get_by_email(email: str, db: AsyncSession):
    result = await db.execute(select(models.User).where(models.User.email == email))
    return result.scalars().first()


async def get_all(db: AsyncSession):
    result = await db.execute(select(models.User))
    return result.scalars().all()


async def create(user: schemas.UserCreate, db: AsyncSession):
    hashed_password = await run_in_threadpool(hash_password, user.password)
    new_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        role="user",
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def update_role(username: str, role: str, db: AsyncSession):
    user = await get_by_username(username, db)
    if not user:
        return None
    user.role = role
    await db.commit()
    await db.refresh(user)
    return user


async def create_admin(db: AsyncSession, username: str, email: str, password: str):
    if await get_by_username(username, db):
        return
    hashed_password = await run_in_threadpool(hash_password, password)
    admin = models.User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        role="admin",
    )
    db.add(admin)
    await db.commit()