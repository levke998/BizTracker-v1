"""Root API router composition."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.health import router as health_router
from app.modules.finance.presentation.api.router import router as finance_router
from app.modules.imports.presentation.api.router import router as imports_router
from app.modules.inventory.presentation.api.router import router as inventory_router
from app.modules.master_data.presentation.api.router import router as master_data_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(finance_router)
api_router.include_router(imports_router)
api_router.include_router(inventory_router)
api_router.include_router(master_data_router)
