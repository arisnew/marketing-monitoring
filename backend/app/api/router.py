from __future__ import annotations
from fastapi import APIRouter

from app.api.routes import auth, health, monitors, platforms

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(platforms.router)
api_router.include_router(monitors.router)
api_router.include_router(health.router)
