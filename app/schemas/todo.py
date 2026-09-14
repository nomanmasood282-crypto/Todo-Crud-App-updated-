from pydantic import BaseModel, ConfigDict, Field


class TodoBase(BaseModel):
    title: str = Field(min_length=3, max_length=300)
    description: str | None = Field(default=None, max_length=300)


class TodoUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=300)
    description: str | None = Field(default=None, max_length=300)
    completed: bool | None


class TodoOut(BaseModel):
    id: int
    completed: bool
    owner_id: int

    model_config = ConfigDict(from_attributes=True)