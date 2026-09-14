from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app import schemas
from app.database import get_db
from app.rate_limit import limiter
from app.services import user_service

router = APIRouter(prefix="/auth", tags=["Authentication"])
DB_DEPENDENCY = Depends(get_db)


@router.post("/generate_token", response_model=schemas.Token)
@limiter.limit("5/minute")
async def generate_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = DB_DEPENDENCY,
):
    return await user_service.authenticate(form_data.username, form_data.password, db)
