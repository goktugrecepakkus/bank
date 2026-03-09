from fastapi import FastAPI
import os
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from database import engine, Base
from rate_limiter import limiter
from routers import customer, account, ledger, auth, trading, cards

# Uygulama başlarken veritabanı bağlantısı kurulur ve tablolar oluşturulur
print(f"Connecting to database: {engine.url.render_as_string(hide_password=True)}")

app = FastAPI(
    title="Rykard Banking API",
    description="Core Banking System API with Ledger implementation (Moduler Monolith)",
    version="1.0.0",
)

# Rate Limiting setup
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.on_event("startup")
def startup_event():
    try:
        Base.metadata.create_all(bind=engine)
        print("Database connection and table creation successful.")
        
        # IBAN migration: Mevcut hesaplara IBAN ata
        try:
            from sqlalchemy import text, inspect
            inspector = inspect(engine)
            columns = [col['name'] for col in inspector.get_columns('accounts')]
            if 'iban' not in columns:
                with engine.connect() as conn:
                    conn.execute(text("ALTER TABLE accounts ADD COLUMN iban VARCHAR(26) UNIQUE;"))
                    conn.commit()
                    print("[Migration] Added iban column to accounts table.")
            
            # NULL IBAN'lara değer ata
            from models import generate_iban
            from database import SessionLocal
            db = SessionLocal()
            try:
                from sqlalchemy import text as sql_text
                null_ibans = db.execute(sql_text("SELECT id FROM accounts WHERE iban IS NULL")).fetchall()
                if null_ibans:
                    for row in null_ibans:
                        iban = generate_iban()
                        db.execute(sql_text("UPDATE accounts SET iban = :iban WHERE id = :id"), {"iban": iban, "id": row[0]})
                    db.commit()
                    print(f"[Migration] Assigned IBAN to {len(null_ibans)} existing accounts.")
            finally:
                db.close()
        except Exception as mig_err:
            print(f"[Migration] IBAN migration note: {mig_err}")
            
    except Exception as e:
        print("Veritabanı bağlantı hatası:", e)
        
# CORS Ayarları (Frontend'in Backend'e bağlanabilmesi için zorunlu güvenlik ayarı)
# Prod'da CORS_ORIGINS env variable'ında domain listesi tutulmalı (virgülle ayrılmış)
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:8000,http://localhost:3000,http://127.0.0.1:8000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi import Request
import traceback

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "traceback": traceback.format_exc()}
    )

from fastapi import APIRouter

# Create a master API router strictly for Vercel prefixing
api_router = APIRouter(prefix="/api")

# Attach all sub-routers to the master /api router
api_router.include_router(auth.router)
api_router.include_router(customer.router)
api_router.include_router(account.router)
api_router.include_router(ledger.router)
api_router.include_router(trading.router)
api_router.include_router(cards.router)

# Include the master router into the main FastAPI application
app.include_router(api_router)

@app.get("/health")
def health_check():
    return JSONResponse(status_code=200, content={"status": "healthy", "service": "banking-api"})

@app.get("/api/debug")
def debug_info():
    """Vercel deployment debug endpoint"""
    import sys
    info = {
        "python_version": sys.version,
        "platform": sys.platform,
        "vercel": os.getenv("VERCEL", "not set"),
    }
    
    # Test database
    try:
        from database import engine
        info["db_url"] = engine.url.render_as_string(hide_password=True)
        with engine.connect() as conn:
            conn.close()
        info["db_status"] = "connected"
    except Exception as e:
        info["db_status"] = f"FAILED: {e}"
    
    # Test bcrypt
    try:
        from passlib.context import CryptContext
        pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
        hashed = pwd.hash("test123")
        verified = pwd.verify("test123", hashed)
        info["bcrypt_status"] = f"OK (verified={verified})"
    except Exception as e:
        info["bcrypt_status"] = f"FAILED: {e}"
    
    # Test bcrypt version
    try:
        import bcrypt
        info["bcrypt_version"] = bcrypt.__version__
    except Exception as e:
        info["bcrypt_version"] = f"FAILED: {e}"
        
    return JSONResponse(status_code=200, content=info)



# Dynamically construct frontend path and mount safely
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "public"))
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
else:
    print(f"Warning: Public directory not found at {frontend_path}. Static files will not be served.")

# Trigger Vercel Deploy 2026-03-10-2
