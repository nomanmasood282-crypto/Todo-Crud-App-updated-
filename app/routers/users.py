from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app import schemas
from app.database import get_db
from app.auth.dependencies import require_admin
from app import schemas
from app.rate_limit import limiter
from app.services import user_service

router = APIRouter(prefix="/users", tags=["Users"])
db_dependency = Depends(get_db)


@router.post("/", response_model=schemas.UserOut)
@limiter.limit("5/minute")
async def register(
    request: Request, user: schemas.UserCreate, db: AsyncSession = db_dependency
):
    return await user_service.register(user, db)


@router.patch("/{username}/role", response_model=schemas.UserOut)
async def update_role(
    username: str,
    data: schemas.UserRoleUpdate,
    db: AsyncSession = db_dependency,
    current_user=Depends(require_admin),
):
    return await user_service.update_role(username, data.role, db)

