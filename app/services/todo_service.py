from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.repositories import todo_repository


async def create(todo: schemas.TodoBase, owner_id: int, db: AsyncSession):
    return await todo_repository.create(todo, owner_id, db)


async def get_by_owner(owner_id: int, db: AsyncSession):
    return await todo_repository.get_by_owner(owner_id, db)


async def get_all(db: AsyncSession):
    return await todo_repository.get_all(db)


async def get_owned(todo_id: int, owner_id: int, db: AsyncSession):
    todo = await todo_repository.get_by_id(todo_id, db)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    if todo.owner_id != owner_id:
        raise HTTPException(status_code=403, detail="Not your todo")
    return todo


async def update(db_todo: models.Todo, todo: schemas.TodoUpdate, db: AsyncSession):
    return await todo_repository.update(db_todo, todo, db)


async def delete(db_todo: models.Todo, db: AsyncSession):
    return await todo_repository.delete(db_todo, db)