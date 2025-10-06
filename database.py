from sqlmodel import SQLModel, create_engine, Session
from config import settings
import os

# Create engine based on database URL
if settings.database_url.startswith("sqlite"):
    # SQLite configuration
    engine = create_engine(
        settings.database_url, 
        connect_args={"check_same_thread": False}
    )
else:
    # PostgreSQL configuration
    engine = create_engine(settings.database_url)

def create_db_and_tables():
    """Create database tables"""
    try:
        SQLModel.metadata.create_all(engine)
        print("✅ Database tables created successfully!")
    except Exception as e:
        print(f"❌ Database creation failed: {e}")
        # For development, we'll continue without failing
        pass

def get_session():
    with Session(engine) as session:
        yield session

# Ensure upload directory exists
os.makedirs(settings.upload_dir, exist_ok=True)
