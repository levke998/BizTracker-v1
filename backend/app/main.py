"""Application entry point for the BizTracker FastAPI backend."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.weather_automation import (
    WeatherAutomationConfig,
    WeatherAutomationService,
)

settings = get_settings()


weather_automation = WeatherAutomationService(
    WeatherAutomationConfig(
        enabled=settings.weather_automation_enabled,
        initial_delay_seconds=settings.weather_automation_initial_delay_seconds,
        interval_minutes=settings.weather_automation_interval_minutes,
        days_back=settings.weather_automation_days_back,
        forecast_days=settings.weather_automation_forecast_days,
    )
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    weather_automation.start()
    try:
        yield
    finally:
        await weather_automation.stop()


app = FastAPI(title=settings.app_name, lifespan=lifespan)

if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.api_v1_prefix)
