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

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Define Rate Limiter (IP based)
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

app = FastAPI(
    title="Rykard Banking API",
    description="Core Banking System API with Ledger implementation (Moduler Monolith)",
    version="1.0.0",
)

# Register Limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Ayarları (Frontend'in Backend'e bağlanabilmesi için zorunlu güvenlik ayarı)
# In production on Vercel, this should ideally be strict.
# Allowing * for easy local test, but strict methods/headers according to security guidelines.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Expand this to actual Vercel domains later
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# API Yollarını (Routers) Ana Uygulamaya Bağlama
app.include_router(auth.router)
app.include_router(customer.router)
app.include_router(account.router)
app.include_router(ledger.router)
app.include_router(trading.router)

@app.get("/health")
def health_check():
    return JSONResponse(status_code=200, content={"status": "healthy", "service": "banking-api"})

app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")
