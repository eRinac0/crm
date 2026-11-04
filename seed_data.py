"""Add demo users, clients, and tasks to the local SQLite database."""

from sqlalchemy import func, select

from app.database import Base, SessionLocal, engine
from app.models import Client, Task, User
from app.schemas import TaskStatus


Base.metadata.create_all(bind=engine)

with SessionLocal() as db:
    for i in range(1, 21):
        email = f"user{i:02}@example.com"
        user = db.scalar(select(User).where(User.email == email))
        if user is None:
            db.add(User(name=f"User {i:02}", email=email))

        email = f"client{i:02}@example.com"
        client = db.scalar(select(Client).where(Client.email == email))
        if client is None:
            db.add(
                Client(
                    name=f"Client {i:02}",
                    email=email,
                    phone=f"+49 30 555 {i:04}",
                    company=f"Company {i:02}",
                    notes=f"Demo CRM client {i:02}",
                )
            )

    db.flush()
    users = db.scalars(select(User).order_by(User.id)).all()
    clients = db.scalars(select(Client).order_by(Client.id)).all()
    statuses = list(TaskStatus)

    tasks = db.scalars(select(Task).order_by(Task.id)).all()
    while len(tasks) < 20:
        i = len(tasks) + 1
        task = Task(
            title=f"Task {i:02}",
            description=f"CRM follow-up task {i:02}",
            status=statuses[(i - 1) % len(statuses)].value,
            user_id=users[(i - 1) % len(users)].id,
            client_id=clients[(i - 1) % len(clients)].id,
        )
        db.add(task)
        tasks.append(task)

    for i, user in enumerate(users, start=1):
        user.name = f"User {i:02}"
    for i, client in enumerate(clients, start=1):
        client.name = f"Client {i:02}"
        client.company = f"Company {i:02}"
        client.notes = f"Demo CRM client {i:02}"
    for i, task in enumerate(tasks, start=1):
        task.title = f"Task {i:02}"
        task.description = f"CRM follow-up task {i:02}"
        task.status = statuses[(i - 1) % len(statuses)].value
        task.user_id = users[(i - 1) % len(users)].id
        task.client_id = clients[(i - 1) % len(clients)].id

    db.commit()

    print(
        "Records in the database:",
        f"users={db.scalar(select(func.count()).select_from(User))},",
        f"clients={db.scalar(select(func.count()).select_from(Client))},",
        f"tasks={db.scalar(select(func.count()).select_from(Task))}",
    )
