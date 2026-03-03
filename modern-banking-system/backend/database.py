import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# .env dosyasını yükle (lokal geliştirme için gerekli, Vercel'de ortam değişkenleri dashboard'dan gelir)
_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(_env_path)

# Default to SQLite for easy local development, use PostgreSQL if DATABASE_URL is provided
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./bank.db")

print(f"[DB] DATABASE_URL loaded: {'Yes (postgresql)' if DATABASE_URL.startswith('postgres') else 'No — using SQLite fallback!'}")
print(f"[DB] Running on Vercel: {os.getenv('VERCEL', 'No')}")

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
    with engine.connect() as conn:
        conn.close()
    print(f"[DB] Successfully connected to: {engine.url.render_as_string(hide_password=True)}")
except Exception as e:
    print(f"[DB] ERROR: Database connection failed with URL: {DATABASE_URL[:30]}... Error: {e}")
    
    # Vercel'de PostgreSQL bağlantısı BAŞARISIZ olursa, sessizce SQLite'a düşME.
    # Bu, verilerin kaybolmasına neden olur!
    if os.getenv("VERCEL") == "1":
        raise Exception(
            f"CRITICAL: Supabase/PostgreSQL connection FAILED on Vercel! "
            f"Check DATABASE_URL environment variable in Vercel Dashboard. "
            f"Error: {e}"
        )
    
    if DATABASE_URL.startswith("postgresql"):
        raise Exception(f"Supabase/PostgreSQL Connection Failed: {e}")
    
    # Sadece lokal geliştirmede SQLite fallback'e izin ver
    print("[DB] Falling back to local SQLite (local development only)...")
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
