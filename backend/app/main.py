"""
FastAPI main application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os

from app.database import engine, Base
from app.routers import auth, datasets, purchases, admin

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Helpuvio API",
    description="B2B Lead Data Marketplace API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://helpuvio.com")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", FRONTEND_URL).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    # CRITICAL: Add these headers to fix COOP errors
    max_age=3600,
)

# Add security headers middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    
    # Remove or relax COOP for OAuth to work
    # Don't set Cross-Origin-Opener-Policy for auth routes
    if not request.url.path.startswith("/api/v1/auth/google"):
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin-allow-popups"
    
    # Add other security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    return response


# Health check endpoint
@app.get("/health")
@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "helpuvio-api"}


# Include routers
app.include_router(auth.router)
# app.include_router(datasets.router)
# app.include_router(purchases.router)
# app.include_router(admin.router)


# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Helpuvio API",
        "version": "1.0.0",
        "docs": "/docs"
    }


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "detail": "Endpoint not found",
            "path": str(request.url.path),
            "method": request.method
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)