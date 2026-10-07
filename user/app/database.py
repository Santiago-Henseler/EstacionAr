from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import DATABASE_URL



engine = create_engine(DATABASE_URL)


session_local = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

def get_db():
    database = session_local()
    try:
        yield database
    finally:
        database.close()