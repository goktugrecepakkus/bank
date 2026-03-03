import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Default to SQLite for easy local development, use PostgreSQL if DATABASE_URL is provided
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./bank.db")

# Automatically fix Supabase/Vercel legacy postgres:// URLs to be compatible with SQLAlchemy 1.4+
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Vercel Serverless environment is completely read-only except for the /tmp folder.
# If no Postgres URL is provided and we are falling back to SQLite on Vercel, we MUST use /tmp.
if os.getenv("VERCEL") == "1" and DATABASE_URL.startswith("sqlite"):
    import shutil
    tmp_db_path = "/tmp/bank.db"
    if not os.path.exists(tmp_db_path) and os.path.exists("./bank.db"):
        try:
            shutil.copy2("./bank.db", tmp_db_path)
        except Exception as e:
            print("Failed to copy bank.db to /tmp:", e)
    DATABASE_URL = f"sqlite:///{tmp_db_path}"

# Detect if we should use SQLite (needed for check_same_thread)
IS_SQLITE = DATABASE_URL.startswith("sqlite")

connect_args = {"check_same_thread": False} if IS_SQLITE else {}

try:
    engine = create_engine(DATABASE_URL, connect_args=connect_args)
    # Test if the dialect/driver is available
    engine.connect().close()
except Exception as e:
    print(f"Database connection error with {DATABASE_URL}: {e}")
    if DATABASE_URL.startswith("postgresql"):
        raise Exception(f"Supabase/PostgreSQL Connection Failed: {e}")
    
    print("Falling back to local SQLite...")
    if os.getenv("VERCEL") == "1":
        import shutil
        tmp_db_path = "/tmp/bank.db"
        if not os.path.exists(tmp_db_path) and os.path.exists("./bank.db"):
            try:
                shutil.copy2("./bank.db", tmp_db_path)
            except Exception as copy_e:
                print("Failed to copy bank.db to /tmp:", copy_e)
        DATABASE_URL = f"sqlite:///{tmp_db_path}"
    else:
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
