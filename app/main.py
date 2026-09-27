import uvicorn
from fastapi import FastAPI
from .schemas import ClientCreate, ClientRead, ClientBase


clients = [
    {
        "id": 1,
        "name": "Alex",
        "email": "alex@example.com"
    }
]


app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "ClientFlow API"}    


@app.get("/health")
def read_item():
    return {"status": "ok"}


@app.get("/clients")
def get_clients():
    return clients

@app.get("/clients/{client_id}")
def get_client(client_id: int):
    client = next((c for c in clients if c["id"] == client_id), None)
    if client is None:
        return {"error": "Client not found"}
    return client

@app.post("/clients")
def create_client(client: ClientBase):
    clients.append(client.dict())
    return client

@app.put("/clients")
def update_client(client: ClientBase):
    for c in clients:
        if c["id"] == client.id:
            c.update(client.dict())
            return c
    return {"error": "Client not found"}

@app.delete("/clients/{client_id}")
def delete_client(client_id: int):
    global clients
    clients = [c for c in clients if c["id"] != client_id]
    return {"message": "Client deleted"}