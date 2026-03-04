from .config import settings

from sqlalchemy.orm import sessionmaker,declarative_base
from sqlalchemy import create_engine


engine = create_engine(settings.DB_URL)

SessionLocal = sessionmaker(bind=engine,autoflush=False,autocommit=False)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()