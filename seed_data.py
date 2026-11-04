"""Add demo users, clients, and tasks to the local SQLite database."""

from sqlalchemy import func, select

from app.database import Base, SessionLocal, engine
from app.models import Client, Task, User
from app.schemas import TaskStatus


Base.metadata.create_all(bind=engine)

with SessionLocal() as db:
    for i in range(1, 21):
        email = f"user{i:02}@example.com"
        if db.scalar(select(User).where(User.email == email)) is None:
            db.add(User(name=f"Пользователь {i:02}", email=email))

        email = f"client{i:02}@example.com"
        if db.scalar(select(Client).where(Client.email == email)) is None:
            db.add(
                Client(
                    name=f"Клиент {i:02}",
                    email=email,
                    phone=f"+49 30 555 {i:04}",
                    company=f"Компания {i:02}",
                    notes=f"Демо-клиент CRM №{i:02}",
                )
            )

    db.flush()
    users = db.scalars(select(User).order_by(User.id)).all()
    clients = db.scalars(select(Client).order_by(Client.id)).all()
    statuses = list(TaskStatus)

    for i in range(1, 21):
        title = f"Демо-задача {i:02}"
        if db.scalar(select(Task).where(Task.title == title)) is None:
            db.add(
                Task(
                    title=title,
                    description=f"Учебная задача CRM №{i:02}",
                    status=statuses[(i - 1) % len(statuses)].value,
                    user_id=users[(i - 1) % len(users)].id,
                    client_id=clients[(i - 1) % len(clients)].id,
                )
            )

    db.commit()

    print(
        "Записей в базе:",
        f"пользователи={db.scalar(select(func.count()).select_from(User))},",
        f"клиенты={db.scalar(select(func.count()).select_from(Client))},",
        f"задачи={db.scalar(select(func.count()).select_from(Task))}",
    )
