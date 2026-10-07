from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str] = mapped_column(String(20))
    company: Mapped[str] = mapped_column(String(100))
    notes: Mapped[str] = mapped_column(String(500))
    tasks: Mapped[list["Task"]] = relationship(
    back_populates="client"
)
    
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(100))

    email: Mapped[str] = mapped_column(String(255))

    tasks: Mapped[list["Task"]] = relationship(
        back_populates="user"
    )

class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)

    title: Mapped[str] = mapped_column(String(200))

    description: Mapped[str] = mapped_column(String(1000))

    status: Mapped[str] = mapped_column(String(50))

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id")
    )

    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id")
    )

    user: Mapped["User"] = relationship(
        back_populates="tasks"
    )

    client: Mapped["Client"] = relationship(
        back_populates="tasks"
    )