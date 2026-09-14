from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app import models, schemas


async def get_by_owner(owner_id: int, db: AsyncSession):
    result = await db.execute(select(models.Todo).where(models.Todo.owner_id == owner_id))
    return result.scalars().all()


async def get_all(db: AsyncSession):
    result = await db.execute(select(models.Todo))
    return result.scalars().all()


async def get_by_id(todo_id: int, db: AsyncSession):
    result = await db.execute(select(models.Todo).where(models.Todo.id == todo_id))
    return result.scalars().first()


async def create(todo: schemas.TodoBase, owner_id: int, db: AsyncSession):
    new_todo = models.Todo(
        title=todo.title, description=todo.description, owner_id=owner_id
    )
    db.add(new_todo)
    await db.commit()
    await db.refresh(new_todo)
    return new_todo


async def update(
    db_todo: models.Todo, todo: schemas.TodoUpdate, db: AsyncSession
):
    for field, value in todo.model_dump(exclude_unset=True).items():
        setattr(db_todo, field, value)
    db.add(db_todo)
    await db.commit()
    await db.refresh(db_todo)
    return db_todo


async def delete(db_todo: models.Todo, db: AsyncSession):
    await db.delete(db_todo)
    await db.commit()