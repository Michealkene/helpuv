from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from app.core.config import settings
from app.routers import auth, datasets, purchases, downloads, admin, webhooks, cart

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting B2B Lead Data Marketplace API...")
    yield
    # Shutdown
    print("👋 Shutting down...")

# Create FastAPI app
app = FastAPI(
    title="B2B Lead Data Marketplace API",
    description="Purchase and download company lead datasets",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with both /api and /api/v1 prefixes for backward compatibility
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(datasets.router, prefix="/api/datasets", tags=["Datasets"])
app.include_router(purchases.router, prefix="/api/purchases", tags=["Purchases"])
app.include_router(downloads.router, prefix="/api/downloads", tags=["Downloads"])
app.include_router(cart.router, prefix="/api/cart", tags=["Cart"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["Webhooks"])

# Also include v1 routes for backward compatibility
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(datasets.router, prefix="/api/v1/datasets", tags=["Datasets"])
app.include_router(purchases.router, prefix="/api/v1/purchases", tags=["Purchases"])
app.include_router(downloads.router, prefix="/api/v1/downloads", tags=["Downloads"])
app.include_router(cart.router, prefix="/api/v1/cart", tags=["Cart"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["Webhooks"])

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }

# Root endpoint
@app.get("/")
async def root():
    return {
        "name": "B2B Lead Data Marketplace API",
        "version": "1.0.0",
        "docs": "/docs"
    }

# Custom 404 error handler
@app.exception_handler(404)
async def custom_404_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": f"The endpoint '{request.url.path}' does not exist.",
            "suggestion": "Check the API documentation at /docs for available endpoints."
        }
    )

# Validation error handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "message": "Invalid request data",
            "details": exc.errors()
        }
    )