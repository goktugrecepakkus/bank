from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .database import engine, Base
from .routers import customer, account, ledger, auth, trading

# Uygulama başlarken veritabanı bağlantısı kurulur ve tablolar oluşturulur
print(f"Connecting to database: {engine.url.render_as_string(hide_password=True)}")

app = FastAPI(
    title="Rykard Banking API",
    description="Core Banking System API with Ledger implementation (Moduler Monolith)",
    version="1.0.0",
)

@app.on_event("startup")
def startup_event():
    try:
        Base.metadata.create_all(bind=engine)
        print("Database connection and table creation successful.")
    except Exception as e:
        print("Veritabanı bağlantı hatası:", e)
        
# CORS Ayarları (Frontend'in Backend'e bağlanabilmesi için zorunlu güvenlik ayarı)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Geliştirme aşaması için herkese açık, prod'da domain yazılır
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
        from .database import engine
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

import os

# Dynamically construct frontend path and mount safely
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "public"))
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
else:
    print(f"Warning: Public directory not found at {frontend_path}. Static files will not be served.")
