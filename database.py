from sqlmodel import SQLModel, create_engine, Session
from config import settings
import os

# ✅ Create engine once
engine = create_engine(
    settings.database_url,
    echo=True,  # shows SQL logs in console (remove in production)
    future=True
)

def create_db_and_tables():
    """Initialize database and create tables."""
    SQLModel.metadata.create_all(engine)

def get_session():
    """Provide a database session."""
    with Session(engine) as session:
        yield session

# ✅ Ensure upload directory exists
if not os.path.exists(settings.upload_dir):
    os.makedirs(settings.upload_dir, exist_ok=True)
