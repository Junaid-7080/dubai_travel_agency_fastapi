import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

# local dev-ക്ക് .env load ചെയ്യാം
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URL set ചെയ്‌തില്ല. Render-ൽ check ചെയ്യുക.")

# postgres:// issue fix
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)

engine = create_engine(DATABASE_URL, echo=True, future=True)
