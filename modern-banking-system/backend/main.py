from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from routers import customer, account, ledger, auth

# Uygulama başlarken veritabanı tablolarını oluşturur
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print("Veritabanı bağlantı uyarısı (Docker çalışmıyor olabilir):", e)

app = FastAPI(
    title="Modern Banking API",
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

# API Yollarını (Routers) Ana Uygulamaya Bağlama
app.include_router(auth.router)
app.include_router(customer.router)
app.include_router(account.router)
app.include_router(ledger.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Modern Banking System API! Go to /docs for Swagger UI"}

@app.get("/health")
def health_check():
    return JSONResponse(status_code=200, content={"status": "healthy", "service": "banking-api"})
