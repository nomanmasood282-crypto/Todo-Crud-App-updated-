from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    username: str = Field(min_length=3, max_length=30)
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(min_length=5, max_length=30)


class UserOut(UserBase):
    id: int
    role: str
    model_config = ConfigDict(from_attributes=True)


class TokenRequest(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserRoleUpdate(BaseModel):
    role: str