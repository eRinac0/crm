from pydantic import BaseModel, EmailStr
from enum import Enum

class ClientBase(BaseModel):
    name: str
    email: EmailStr
    phone: str
    company: str
    notes: str


class ClientCreate(ClientBase):
    pass

class ClientRead(ClientBase):
    id: int


class UserCreate(BaseModel):
    name: str
    email: EmailStr

class UserRead(UserCreate):
    id: int

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    
class TaskCreate(BaseModel):
    title: str
    description: str
    status: TaskStatus
    user_id: int
    client_id: int

class TaskRead(TaskCreate):
    id: int

class TaskUpdate(TaskCreate):
    pass

class SortField(str, Enum):
    ID = "id"
    TITLE = "title"
    STATUS = "status"
    USER_ID = "user_id"
    CLIENT_ID = "client_id"

class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"
