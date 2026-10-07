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
    