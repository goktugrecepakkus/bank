import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Default to SQLite for easy local development, use PostgreSQL if DATABASE_URL is provided
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./bank.db")

# Detect if we should use SQLite (needed for check_same_thread)
IS_SQLITE = DATABASE_URL.startswith("sqlite")

connect_args = {"check_same_thread": False} if IS_SQLITE else {}

try:
    engine = create_engine(DATABASE_URL, connect_args=connect_args)
    # Test if the dialect/driver is available
    engine.connect().close()
except Exception as e:
    print(f"Database connection error with {DATABASE_URL}: {e}")
    print("Falling back to local SQLite (bank.db)...")
    DATABASE_URL = "sqlite:///./bank.db"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency for FastAPI to get DB sessions
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
