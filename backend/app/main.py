# helpuvio/backend/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import os

app = FastAPI(
    title="Helpuvio API",
    description="Dataset marketplace and analytics platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# ============================================
# CORS Configuration
# ============================================
# Get allowed origins from environment or use defaults
allowed_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
if not allowed_origins or allowed_origins == [""]:
    allowed_origins = [
        "http://localhost:5173",
        "http://localhost:3000",
        "https://helpuvio.com",
        "https://www.helpuvio.com",
        "https://api.helpuvio.com",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ============================================
# Compression Middleware
# ============================================
app.add_middleware(GZipMiddleware, minimum_size=1000)

# ============================================
# Health Check Endpoint
# ============================================
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "helpuvio-backend",
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    return {
        "message": "Helpuvio API",
        "docs": "/docs",
        "health": "/health"
    }

# ============================================
# Include Routers
# ============================================
from app.routers import datasets, auth

app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(datasets.router, prefix="/api/v1/datasets", tags=["datasets"])

from app.routers import email_verification

# Include router
app.include_router(
    email_verification.router, 
    prefix="/api/v1/emails", 
    tags=["Email Verification"]
)

# Uncomment these when you create the router files:
# from app.routers import users, transactions
# app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
# app.include_router(transactions.router, prefix="/api/v1/transactions", tags=["transactions"])

# ============================================
# Startup Event
# ============================================
@app.on_event("startup")
async def startup_event():
    print("🚀 Helpuvio Backend starting...")
    print(f"📍 CORS enabled for: {allowed_origins}")
    print(f"🌍 Environment: {os.getenv('ENVIRONMENT', 'development')}")

@app.on_event("shutdown")
async def shutdown_event():
    print("👋 Helpuvio Backend shutting down...")