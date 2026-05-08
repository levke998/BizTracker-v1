"""Root API router composition."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.health import router as health_router
from app.modules.analytics.presentation.api.router import router as analytics_router
from app.modules.catalog.presentation.api.router import router as catalog_router
from app.modules.demo_pos.presentation.api.router import router as demo_pos_router
from app.modules.events.presentation.api.router import router as events_router
from app.modules.finance.presentation.api.router import router as finance_router
from app.modules.identity.presentation.api.router import router as identity_router
from app.modules.imports.presentation.api.router import router as imports_router
from app.modules.inventory.presentation.api.router import router as inventory_router
from app.modules.master_data.presentation.api.router import router as master_data_router
from app.modules.pos_ingestion.presentation.api.router import router as pos_ingestion_router
from app.modules.procurement.presentation.api.router import router as procurement_router
from app.modules.production.presentation.api.router import router as production_router
from app.modules.weather.presentation.api.router import router as weather_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(analytics_router)
api_router.include_router(catalog_router)
api_router.include_router(demo_pos_router)
api_router.include_router(events_router)
api_router.include_router(finance_router)
api_router.include_router(identity_router)
api_router.include_router(imports_router)
api_router.include_router(inventory_router)
api_router.include_router(master_data_router)
api_router.include_router(pos_ingestion_router)
api_router.include_router(procurement_router)
api_router.include_router(production_router)
api_router.include_router(weather_router)
