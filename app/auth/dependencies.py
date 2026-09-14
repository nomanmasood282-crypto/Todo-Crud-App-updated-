from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import decode_access_token
from app.database import get_db
from app.repositories import user_repository

bearer_scheme = HTTPBearer()
credentials_dependency = Depends(bearer_scheme)
db_dependency = Depends(get_db)


async def get_current_users(
    credentials: HTTPAuthorizationCredentials = credentials_dependency,
    db: AsyncSession = db_dependency,
):
    payload = decode_access_token(credentials.credentials)
    username = payload.get("sub") if payload else None

    user = await user_repository.get_by_username(username, db) if username else None

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials",
        )
    return user


async def require_admin(user=Depends(get_current_users)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user