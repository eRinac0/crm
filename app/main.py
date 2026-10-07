from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.database import get_db, Base, engine
from app.models import Client, User, Task
from app.schemas import ClientCreate, ClientBase, ClientRead, UserCreate, UserRead


app = FastAPI()
Base.metadata.create_all(bind=engine)

@app.get("/")
def read_root():
    return {"message": "Welcome to the CRM API!"}

@app.get("/clients", response_model=list[ClientRead])
def get_clients(db: Session = Depends(get_db)):
    result = db.execute(
        select(Client)
    )

    return result.scalars().all()


@app.post("/clients", response_model=ClientRead)
def create_client(
    client_data: ClientCreate,
    db: Session = Depends(get_db)
):
    client = Client(
        name=client_data.name,
        email=client_data.email,
        phone=client_data.phone,
        company=client_data.company,
        notes=client_data.notes
    )

    db.add(client)
    db.commit()
    db.refresh(client)

    return client


@app.put("/clients/{client_id}")
def update_client(
    client_id: int,
    client_data: ClientBase,
    db: Session = Depends(get_db)
):
    client = db.get(Client, client_id)

    if not client:
        raise HTTPException(
            status_code=404,
            detail="Client not found"
        )

    client.name = client_data.name
    client.email = client_data.email
    client.phone = client_data.phone
    client.company = client_data.company
    client.notes = client_data.notes

    db.commit()
    db.refresh(client)

    return client


@app.delete("/clients/{client_id}")
def delete_client(
    client_id: int,
    db: Session = Depends(get_db)
):
    client = db.get(Client, client_id)

    if not client:
        raise HTTPException(
            status_code=404,
            detail="Client not found"
        )

    db.delete(client)
    db.commit()

    return {"message": "Client deleted successfully"}


@app.post("/users", response_model=UserRead)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    user = User(
        name=user_data.name,
        email=user_data.email
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user