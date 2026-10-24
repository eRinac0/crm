from fastapi import FastAPI, Depends, HTTPException, Query  
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.database import get_db, Base, engine
from app.models import Client, User, Task
from app.schemas import ClientCreate, ClientRead, UserCreate, UserRead, TaskCreate, TaskRead, TaskUpdate, TaskStatus


app = FastAPI()
Base.metadata.create_all(bind=engine)

@app.get("/")
def read_root():
    return {"message": "Welcome to the CRM API!"}

@app.get("/clients", response_model=list[ClientRead])
def get_clients(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    sort_by: str = "id",
    order: str = "asc",
    db: Session = Depends(get_db)
):
    query = select(Client)

    if sort_by == "name":
        column = Client.name
    elif sort_by == "id":
        column = Client.id
    else:
        raise HTTPException(status_code=400, detail="Invalid sort field")

    if order == "desc":
        query = query.order_by(column.desc())
    elif order == "asc":
        query = query.order_by(column.asc())
    else:
        raise HTTPException(status_code=400, detail="Invalid sort order")

    query = query.limit(limit).offset(offset)

    result = db.execute(query)

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
    client_data: ClientRead,
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

@app.post("/tasks", response_model=TaskRead)
def create_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db)
):
    user = db.get(User, task_data.user_id)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
    )
    client = db.get(Client, task_data.client_id)

    if not client:
        raise HTTPException(
            status_code=404,
            detail="Client not found"
    )
    task = Task(
        title=task_data.title,
        description=task_data.description,
        status=task_data.status,
        user_id=task_data.user_id,
        client_id=task_data.client_id
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    return task

@app.get("/tasks", response_model=list[TaskRead])
def get_tasks(db: Session = Depends(get_db)):
    result = db.execute(select(Task))

    return result.scalars().all()


@app.get("/users/{user_id}/tasks", response_model=list[TaskRead])
def get_user_tasks(user_id: int,db: Session = Depends(get_db)):
    user = db.get(User, user_id)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    result = db.execute(select(Task).where(Task.user_id == user_id))

    return result.scalars().all()


@app.get("/tasks/{task_id}", response_model=TaskRead)
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)

    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    return task


@app.put("/tasks/{task_id}", response_model=TaskRead)
def update_task(
    task_id: int,
    task_data: TaskUpdate,
    db: Session = Depends(get_db)
):
    task = db.get(Task, task_id)

    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )
   
    user = db.get(User, task_data.user_id)

    if not user:
        raise HTTPException(
                status_code=404,
                detail="User not found"
            )
    
    
    client = db.get(Client, task_data.client_id)

    if not client:
        raise HTTPException(
                status_code=404,
                detail="Client not found"
            )
    task.title = task_data.title
    task.description = task_data.description
    task.status = task_data.status
    task.user_id = task_data.user_id
    task.client_id = task_data.client_id

    db.commit()
    db.refresh(task)

    return task


@app.delete("/tasks/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db)
):
    task = db.get(Task, task_id)

    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    db.delete(task)
    db.commit()

    return {"message": "Task deleted successfully"}

@app.get("/task/filter", response_model=list[TaskRead])
def filter_tasks(status: TaskStatus | None = None, user_id: int | None = None, client_id: int | None = None, limit: int = Query(default=10, ge=1, le=100),offset: int = Query(default=0, ge=0), db: Session = Depends(get_db)):
    query = select(Task)
    if status is not None:
        query = query.where(Task.status == status)

    if user_id is not None:
        query = query.where(Task.user_id == user_id)

    if client_id is not None:
        query = query.where(Task.client_id == client_id)

    query = query.order_by(Task.id).limit(limit).offset(offset)
    result = db.execute(query)

    return result.scalars().all()

@app.get("/users", response_model=list[UserRead])
def get_users(db: Session = Depends(get_db)):
    result = db.execute(select(User))
    return result.scalars().all()

@app.get("/users/{user_id}", response_model=UserRead)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return user


@app.put("/users/{user_id}", response_model=UserRead)
def update_user(user_id: int, user_data: UserCreate, db: Session = Depends(get_db)):
        user = db.get(User, user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        
        user.name = user_data.name
        user.email = user_data.email
        db.commit()
        db.refresh(user)
        return user

@app.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    
   
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.tasks:
            raise HTTPException(
                status_code=409,
                detail="Cannot delete user with assigned tasks"
            )
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}


@app.get("/clients/search", response_model=list[ClientRead])
def search_clients(name: str|None = None,email: str|None = None, db: Session = Depends(get_db),limit: int = Query(default=10, ge=1, le=100),offset: int = Query(default=0, ge=0)):
    query = select(Client)
    if name:
        query = query.where(func.lower(Client.name).contains(name.lower()))
    if email:
        query = query.where(func.lower(Client.email).contains(email.lower()))
    query = query.order_by(Client.id).limit(limit).offset(offset)
    result = db.execute(query)
    return result.scalars().all()