from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints
from typing import Annotated


ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class ClientBase(BaseModel):
    name: Annotated[ShortText, Field(max_length=100)]
    email: EmailStr
    phone: Annotated[ShortText, Field(max_length=20)]
    company: Annotated[ShortText, Field(max_length=100)]
    notes: Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)] = ""


class ClientCreate(ClientBase):
    pass


class ClientRead(ClientBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class UserCreate(BaseModel):
    name: Annotated[ShortText, Field(max_length=100)]
    email: EmailStr
    password: Annotated[str, Field(min_length=12, max_length=128)]


class RegistrationRequest(UserCreate):
    invitation_key: Annotated[str, Field(min_length=1, max_length=256)]


class UserUpdate(BaseModel):
    name: Annotated[ShortText, Field(max_length=100)]
    email: EmailStr
    password: str | None = Field(default=None, min_length=12, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: Annotated[str, Field(min_length=1, max_length=128)]


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class TaskCreate(BaseModel):
    title: Annotated[ShortText, Field(max_length=200)]
    description: Annotated[str, StringConstraints(strip_whitespace=True, max_length=1000)] = ""
    status: TaskStatus
    user_id: int = Field(gt=0)
    client_id: int = Field(gt=0)


class TaskRead(TaskCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int


class TaskUpdate(TaskCreate):
    pass


class SortField(str, Enum):
    ID = "id"
    NAME = "name"


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


class ClientListResponse(BaseModel):
    items: list[ClientRead]
    total: int
    pages: int
    limit: int
    offset: int
    has_next: bool
