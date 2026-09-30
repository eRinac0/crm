import uvicorn
from fastapi import FastAPI
from .schemas import ClientCreate, ClientRead, ClientBase
from app.database import Base, engine, SessionLocal
from app.models import Client
app = FastAPI()
Base.metadata.create_all(bind=engine)

clients = [
    {
        "id": 1,
        "name": "Alex",
        "email": "alex@example.com"
    }
]


db = SessionLocal()


@app.get("/")
def read_root():
    return {"message": "ClientFlow API"}    


@app.get("/health")
def read_item():
    return {"status": "ok"}


@app.get("/clients")
def get_clients():
    return clients

@app.get("/clients/{client_id}", response_model=ClientRead)
def get_client(client_id: int):
    client = next((c for c in clients if c["id"] == client_id), None)
    if client is None:
        return {"error": "Client not found"}
    return client

@app.post("/clients", response_model=ClientRead)
def create_client(client: ClientBase):
    clients.append(client.dict())
    return client

@app.put("/clients/{client_id}", response_model=ClientRead)
def update_client(client_id: int, client: ClientBase):
    for c in clients:
        if c["id"] == client_id:
            c.update(client.dict())
            return c
    return {"error": "Client not found"}

@app.delete("/clients/{client_id}")
def delete_client(client_id: int):
    global clients
    clients = [c for c in clients if c["id"] != client_id]
    return {"message": "Client deleted"}


@app.get("/clients", response_model=list[ClientRead])
async def search_clients(name: str = None, email: str = None):
    results = clients
    if name:
        results = [c for c in results if name.lower() in c["name"].lower()]
    if email:
        results = [c for c in results if email.lower() in c["email"].lower()]
    return results