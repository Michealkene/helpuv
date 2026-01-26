"""
API Routers package
"""

from app.routers.auth import router as auth_router
from app.routers.datasets import router as datasets_router
from app.routers.purchases import router as purchases_router
from app.routers.downloads import router as downloads_router
from app.routers.webhooks import router as webhooks_router
from app.routers.admin import router as admin_router
from app.routers.companies import router as companies_router

__all__ = [
    "auth_router",
    "datasets_router",
    "purchases_router",
    "downloads_router",
    "webhooks_router",
    "admin_router",
    "companies_router"
]
