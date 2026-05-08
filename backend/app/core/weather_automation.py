"""Built-in background weather automation for the backend process."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import UTC, datetime

from app.db.session import SessionLocal
from app.modules.weather.application.commands.backfill_weather import (
    BackfillWeatherCommand,
)
from app.modules.weather.application.commands.sync_shared_weather import (
    SyncSharedWeatherCommand,
)
from app.modules.weather.application.commands.sync_shared_weather_forecast import (
    SyncSharedWeatherForecastCommand,
)
from app.modules.weather.application.services.weather_provider import (
    OpenMeteoWeatherProvider,
)
from app.modules.weather.infrastructure.repositories.sqlalchemy_weather_repository import (
    SqlAlchemyWeatherRepository,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class WeatherAutomationConfig:
    """Configuration for built-in weather automation."""

    enabled: bool
    initial_delay_seconds: int
    interval_minutes: int
    days_back: int
    forecast_days: int


class WeatherAutomationService:
    """Runs non-blocking, idempotent weather sync jobs inside the backend."""

    def __init__(self, config: WeatherAutomationConfig) -> None:
        self._config = config
        self._task: asyncio.Task[None] | None = None
        self._stop_event: asyncio.Event | None = None

    def start(self) -> None:
        if not self._config.enabled:
            logger.info("Weather automation is disabled.")
            return
        if self._task is not None and not self._task.done():
            return

        self._stop_event = asyncio.Event()
        self._task = asyncio.create_task(
            self._run_loop(),
            name="biztracker-weather-automation",
        )
        logger.info(
            "Weather automation started: interval=%s minutes, days_back=%s, forecast_days=%s",
            self._config.interval_minutes,
            self._config.days_back,
            self._config.forecast_days,
        )

    async def stop(self) -> None:
        if self._task is None:
            return

        if self._stop_event is not None:
            self._stop_event.set()
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        finally:
            self._task = None
            self._stop_event = None

    async def _run_loop(self) -> None:
        await self._sleep_or_stop(self._config.initial_delay_seconds)
        while True:
            await asyncio.to_thread(self._run_once)
            await self._sleep_or_stop(self._config.interval_minutes * 60)

    async def _sleep_or_stop(self, seconds: int) -> None:
        if self._stop_event is None:
            return
        try:
            await asyncio.wait_for(self._stop_event.wait(), timeout=max(seconds, 0))
        except TimeoutError:
            return
        raise asyncio.CancelledError

    def _run_once(self) -> None:
        started_at = datetime.now(UTC)
        logger.info("Weather automation cycle started at %s", started_at.isoformat())
        try:
            with SessionLocal() as session:
                repository = SqlAlchemyWeatherRepository(session)
                provider = OpenMeteoWeatherProvider()
                observation_result = SyncSharedWeatherCommand(
                    backfill_command=BackfillWeatherCommand(
                        repository=repository,
                        provider=provider,
                    )
                ).execute(days_back=self._config.days_back)
                forecast_result = SyncSharedWeatherForecastCommand(
                    repository=repository,
                    provider=provider,
                ).execute(forecast_days=self._config.forecast_days)
        except Exception:
            logger.exception("Weather automation cycle failed.")
            return

        logger.info(
            "Weather automation cycle completed: observations created=%s updated=%s skipped=%s; forecasts created=%s updated=%s",
            observation_result.created_count,
            observation_result.updated_count,
            observation_result.skipped_count,
            forecast_result.created_count,
            forecast_result.updated_count,
        )
