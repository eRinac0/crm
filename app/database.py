from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


DATABASE_URL = "sqlite:///./database.db"


engine = create_engine(DATABASE_URL)


SessionLocal = sessionmaker(
    bind=engine
)

def get_db():
    db = SessionLocal()

    try:    
        yield db
    finally:
        db.close()

class Base(DeclarativeBase):
    pass    