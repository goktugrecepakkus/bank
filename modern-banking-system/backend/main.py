from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from database import engine, Base
from routers import customer, account, ledger, auth, trading

# Uygulama başlarken veritabanı bağlantısı kurulur ve tablolar oluşturulur
print(f"Connecting to database: {engine.url.render_as_string(hide_password=True)}")
try:
    Base.metadata.create_all(bind=engine)
    print("Database connection and table creation successful.")
except Exception as e:
    print("Veritabanı bağlantı hatası:", e)

app = FastAPI(
    title="Rykard Banking API",
    description="Core Banking System API with Ledger implementation (Moduler Monolith)",
    version="1.0.0",
)

# CORS Ayarları (Frontend'in Backend'e bağlanabilmesi için zorunlu güvenlik ayarı)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Geliştirme aşaması için herkese açık, prod'da domain yazılır
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

import os

# Dynamically construct frontend path and mount safely
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
else:
    print(f"Warning: Frontend directory not found at {frontend_path}. Static files will not be served.")
