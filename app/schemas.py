from pydantic import BaseModel, EmailStr

class ClientBase(BaseModel):
    name: str
    email: EmailStr
    phone: int


class ClientCreate(ClientBase):
    pass

class ClientRead(ClientBase):
    id: int