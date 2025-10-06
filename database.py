from sqlmodel import SQLModel, create_engine, Session
from config import DATABASE_URL

# Create engine
engine = create_engine(DATABASE_URL, echo=True)

# Create tables
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

# Dependency to get database session
def get_session():
    with Session(engine) as session:
        yield session