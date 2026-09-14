from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.database import get_db
from app.auth.dependencies import get_current_users, require_admin
from app import cache
from app.rate_limit import limiter
from app.services import todo_service

router = APIRouter(prefix="/todos", tags=["Todos"])
db_dependency = Depends(get_db)
user_dependency = Depends(get_current_users)


@router.post("/", response_model=schemas.TodoOut)
@limiter.limit("30/minute")
async def create_todo(
    request: Request,
    todo: schemas.TodoBase,
    db: AsyncSession = db_dependency,
    current_user: models.User = user_dependency,
):
    result = await todo_service.create(todo, current_user.id, db)
    cache.delete(f"todos:{current_user.id}:list")
    return result


@router.get("/by-owner", response_model=list[schemas.TodoOut])
@limiter.limit("60/minute")
async def list_my_todos(
    request: Request,
    db: AsyncSession = db_dependency,
    current_user: models.User = user_dependency,
):
    key = f"todos:{current_user.id}:list"
    todos = cache.get(key)
    if todos is None:
        todos = await todo_service.get_by_owner(current_user.id, db)
        todos = [schemas.TodoOut.model_validate(todo).model_dump() for todo in todos]
        cache.set(key, todos)
    return todos


@router.get("/all", response_model=list[schemas.TodoOut])
async def list_all_todos(
    db: AsyncSession = db_dependency,
    current_user: models.User = Depends(require_admin),
):
    return await todo_service.get_all(db)


@router.get("/{todo_id}", response_model=schemas.TodoOut)
@limiter.limit("60/minute")
async def get_todo(
    request: Request,
    todo_id: int,
    db: AsyncSession = db_dependency,
    current_user: models.User = user_dependency,
):
    key = f"todos:{current_user.id}:{todo_id}"
    todo = cache.get(key)
    if todo is None:
        todo = await todo_service.get_owned(todo_id, current_user.id, db)

    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    owner_id = todo["owner_id"] if isinstance(todo, dict) else todo.owner_id
    if owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your todo")

    if isinstance(todo, models.Todo):
        todo = schemas.TodoOut.model_validate(todo).model_dump()
        cache.set(key, todo)
    return todo


@router.put("/{todo_id}", response_model=schemas.TodoOut)
@limiter.limit("30/minute")
async def update_todo(
    request: Request,
    todo_id: int,
    todo: schemas.TodoUpdate,
    db: AsyncSession = db_dependency,
    current_user: models.User = user_dependency,
):
    db_todo = await todo_service.get_owned(todo_id, current_user.id, db)

    result = await todo_service.update(db_todo, todo, db)
    cache.delete(f"todos:{current_user.id}:list")
    cache.delete(f"todos:{current_user.id}:{todo_id}")
    return result


@router.delete("/{todo_id}", response_model=schemas.TodoOut)
@limiter.limit("30/minute")
async def delete_todo(
    request: Request,
    todo_id: int,
    db: AsyncSession = db_dependency,
    current_user: models.User = user_dependency,
):
    db_todo = await todo_service.get_owned(todo_id, current_user.id, db)

    await todo_service.delete(db_todo, db)
    cache.delete(f"todos:{current_user.id}:list")
    cache.delete(f"todos:{current_user.id}:{todo_id}")
    return db_todo
