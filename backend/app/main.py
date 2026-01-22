from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

# Import routers
from app.routers import auth, datasets, purchases, downloads, admin, webhooks

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info("🚀 Starting Helpuvio API...")
    yield
    logger.info("👋 Shutting down Helpuvio API...")


# Create FastAPI app
app = FastAPI(
    title="Helpuvio API",
    description="B2B Lead Data Marketplace API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration - CRITICAL FIX
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative frontend port
        "https://helpuvio.com",   # Production domain
        "https://*.helpuvio.com", # Subdomains
        "https://*.vercel.app",   # Vercel preview deployments
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"]
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "service": "helpuvio-api",
        "version": "1.0.0"
    }

# Root endpoint
@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Helpuvio API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(datasets.router, prefix="/api/datasets", tags=["Datasets"])
app.include_router(purchases.router, prefix="/api/purchases", tags=["Purchases"])
app.include_router(downloads.router, prefix="/api/downloads", tags=["Downloads"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["Webhooks"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )