import math
import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.database import get_db
from app.models import Client, Task, User
from app.schemas import (
    ClientCreate,
    ClientListResponse,
    ClientRead,
    LoginRequest,
    RegistrationRequest,
    SortField,
    SortOrder,
    TaskCreate,
    TaskRead,
    TaskStatus,
    TaskUpdate,
    TokenResponse,
    UserRead,
    UserUpdate,
)
from app.security import (
    ACCESS_TOKEN_TTL_SECONDS,
    DUMMY_PASSWORD_HASH,
    create_access_token,
    hash_password,
    verify_access_token,
    verify_password,
    verify_registration_key,
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Fail closed instead of starting an API that cannot validate tokens safely.
    create_access_token(1)
    yield


app = FastAPI(title="CRM API", lifespan=lifespan)
allowed_hosts = [
    host.strip()
    for host in os.getenv("CRM_ALLOWED_HOSTS", "localhost,127.0.0.1,testserver").split(",")
    if host.strip()
]
app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)


class RequestSizeLimitMiddleware:
    """Reject oversized request bodies, including chunked requests."""

    max_bytes = 1_048_576

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        content_length = headers.get(b"content-length")
        if content_length:
            try:
                if int(content_length) > self.max_bytes:
                    await self._send_too_large(send)
                    return
            except ValueError:
                await self._send_too_large(send)
                return

        received = 0

        async def limited_receive():
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_bytes:
                    raise RequestTooLarge
            return message

        try:
            await self.app(scope, limited_receive, send)
        except RequestTooLarge:
            await self._send_too_large(send)

    @staticmethod
    async def _send_too_large(send):
        body = b'{"detail":"Request body too large"}'
        await send(
            {
                "type": "http.response.start",
                "status": 413,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode()),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})


class RequestTooLarge(Exception):
    pass


class SecurityHeadersMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        async def add_headers(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.extend(
                    [
                        (b"x-content-type-options", b"nosniff"),
                        (b"x-frame-options", b"DENY"),
                        (b"referrer-policy", b"no-referrer"),
                        (b"permissions-policy", b"camera=(), microphone=(), geolocation=()"),
                        (b"cache-control", b"no-store"),
                    ]
                )
                if scope.get("scheme") == "https":
                    headers.append(
                        (b"strict-transport-security", b"max-age=31536000; includeSubDomains")
                    )
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, add_headers)


app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestSizeLimitMiddleware)


bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    unauthorized = HTTPException(
        status_code=401,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise unauthorized
    user_id = verify_access_token(credentials.credentials)
    user = db.get(User, user_id) if user_id is not None else None
    if user is None:
        raise unauthorized
    return user


@app.get("/")
def read_root():
    return {"message": "CRM API"}


@app.post("/auth/register", response_model=UserRead, status_code=201)
def register_user(data: RegistrationRequest, db: Session = Depends(get_db)):
    if not verify_registration_key(data.invitation_key):
        raise HTTPException(status_code=403, detail="Registration is unavailable")
    normalized_email = str(data.email).casefold()
    existing_user = db.scalar(
        select(User).where(func.lower(User.email) == normalized_email)
    )
    if existing_user:
        raise HTTPException(status_code=409, detail="Email is already registered")

    user = User(
        name=data.name,
        email=normalized_email,
        password_hash=hash_password(data.password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Unable to register this account") from None
    db.refresh(user)
    return user


@app.post("/auth/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    normalized_email = str(data.email).casefold()
    user = db.scalar(select(User).where(func.lower(User.email) == normalized_email))
    # A dummy Argon2 hash keeps unknown-account attempts from skipping password work.
    stored_hash = user.password_hash if user and user.password_hash else DUMMY_PASSWORD_HASH
    password_ok = verify_password(data.password, stored_hash)
    if user is None or user.password_hash is None or not password_ok:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenResponse(
        access_token=create_access_token(user.id),
        expires_in=ACCESS_TOKEN_TTL_SECONDS,
    )


@app.get("/auth/me", response_model=UserRead)
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user


@app.get("/clients", response_model=ClientListResponse)
def get_clients(
    name: str | None = Query(default=None, max_length=100),
    email: str | None = Query(default=None, max_length=255),
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    sort_by: SortField = SortField.ID,
    order: SortOrder = SortOrder.ASC,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    filters = []
    if name:
        filters.append(func.lower(Client.name).contains(name.casefold(), autoescape=True))
    if email:
        filters.append(func.lower(Client.email).contains(email.casefold(), autoescape=True))
    column = Client.name if sort_by == SortField.NAME else Client.id
    ordering = column.desc() if order == SortOrder.DESC else column.asc()
    total = db.scalar(select(func.count()).select_from(Client).where(*filters)) or 0
    items = db.scalars(
        select(Client).where(*filters).order_by(ordering).limit(limit).offset(offset)
    ).all()
    return ClientListResponse(
        items=items,
        total=total,
        pages=math.ceil(total / limit),
        limit=limit,
        offset=offset,
        has_next=offset + limit < total,
    )


@app.post("/clients", response_model=ClientRead, status_code=201)
def create_client(
    data: ClientCreate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    client = Client(**data.model_dump())
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@app.put("/clients/{client_id}", response_model=ClientRead)
def update_client(
    client_id: int,
    data: ClientCreate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    client = db.get(Client, client_id)
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    for field, value in data.model_dump().items():
        setattr(client, field, value)
    db.commit()
    db.refresh(client)
    return client


@app.delete("/clients/{client_id}")
def delete_client(
    client_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    client = db.get(Client, client_id)
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    if client.tasks:
        raise HTTPException(status_code=409, detail="Client has assigned tasks")
    db.delete(client)
    db.commit()
    return {"message": "Client deleted successfully"}


@app.post("/tasks", response_model=TaskRead, status_code=201)
def create_task(
    data: TaskCreate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    if db.get(User, data.user_id) is None:
        raise HTTPException(status_code=404, detail="User not found")
    if db.get(Client, data.client_id) is None:
        raise HTTPException(status_code=404, detail="Client not found")
    task = Task(**data.model_dump())
    task.status = data.status.value
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@app.get("/tasks", response_model=list[TaskRead])
def get_tasks(
    limit: int = Query(default=100, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    return db.scalars(select(Task).order_by(Task.id).limit(limit).offset(offset)).all()


@app.get("/users/{user_id}/tasks", response_model=list[TaskRead])
def get_user_tasks(
    user_id: int,
    limit: int = Query(default=100, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    if db.get(User, user_id) is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db.scalars(
        select(Task).where(Task.user_id == user_id).order_by(Task.id).limit(limit).offset(offset)
    ).all()


@app.get("/tasks/{task_id}", response_model=TaskRead)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.put("/tasks/{task_id}", response_model=TaskRead)
def update_task(
    task_id: int,
    data: TaskUpdate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if db.get(User, data.user_id) is None:
        raise HTTPException(status_code=404, detail="User not found")
    if db.get(Client, data.client_id) is None:
        raise HTTPException(status_code=404, detail="Client not found")
    for field, value in data.model_dump().items():
        setattr(task, field, value.value if isinstance(value, TaskStatus) else value)
    db.commit()
    db.refresh(task)
    return task


@app.delete("/tasks/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return {"message": "Task deleted successfully"}


@app.get("/task/filter", response_model=list[TaskRead])
def filter_tasks(
    status: TaskStatus | None = None,
    user_id: int | None = Query(default=None, gt=0),
    client_id: int | None = Query(default=None, gt=0),
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    query = select(Task)
    if status is not None:
        query = query.where(Task.status == status.value)
    if user_id is not None:
        query = query.where(Task.user_id == user_id)
    if client_id is not None:
        query = query.where(Task.client_id == client_id)
    return db.scalars(query.order_by(Task.id).limit(limit).offset(offset)).all()


@app.get("/users", response_model=list[UserRead])
def get_users(
    limit: int = Query(default=100, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    return db.scalars(select(User).order_by(User.id).limit(limit).offset(offset)).all()


@app.get("/users/{user_id}", response_model=UserRead)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.put("/users/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only update your own account")
    normalized_email = str(data.email).casefold()
    duplicate = db.scalar(
        select(User).where(func.lower(User.email) == normalized_email, User.id != user_id)
    )
    if duplicate:
        raise HTTPException(status_code=409, detail="Email is already registered")
    current_user.name = data.name
    current_user.email = normalized_email
    if data.password is not None:
        current_user.password_hash = hash_password(data.password)
    db.commit()
    db.refresh(current_user)
    return current_user


@app.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only delete your own account")
    if current_user.tasks:
        raise HTTPException(status_code=409, detail="Cannot delete account with assigned tasks")
    db.delete(current_user)
    db.commit()
    return {"message": "Account deleted successfully"}
