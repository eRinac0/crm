from pydantic import BaseModel, EmailStr

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
    
class TaskCreate(BaseModel):
    title: str
    description: str
    status: str
    user_id: int
    client_id: int

class TaskRead(TaskCreate):
    id: int