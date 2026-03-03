import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv() # Load variables from .env file securely

# Default to SQLite for easy local development, use PostgreSQL if DATABASE_URL is provided
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./bank.db")

# Detect if we should use SQLite
IS_SQLITE = DATABASE_URL.startswith("sqlite")

# For Vercel/Supabase, we need pooling and SSL. For SQLite we need check_same_thread
if IS_SQLITE:
    connect_args = {"check_same_thread": False}
    engine = create_engine(DATABASE_URL, connect_args=connect_args)
else:
    # Supabase / PostgreSQL specific connection arguments
    # Avoid connection pool exhaustion in serverless Vercel environments using pool_pre_ping and pool_size
    connect_args = {} # SQLAlchemy usually handles SSL automatically via psycopg2
    try:
        engine = create_engine(
            DATABASE_URL, 
            connect_args=connect_args,
            pool_pre_ping=True, 
            pool_size=5, 
            max_overflow=10
        )
        engine.connect().close()
        print("Connected to remote PostgreSQL (Supabase) successfully.")
    except Exception as e:
        print(f"Database connection error with remote DB: {e}")
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
