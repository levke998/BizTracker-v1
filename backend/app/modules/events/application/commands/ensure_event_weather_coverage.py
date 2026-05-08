"""Ensure weather coverage for Flow event time windows."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import timedelta

from app.modules.events.application.commands.create_event import EventNotFoundError
from app.modules.events.domain.repositories.event_repository import EventRepository
from app.modules.weather.application.commands.ensure_shared_weather_interval_coverage import (
    EnsureSharedWeatherIntervalCoverageCommand,
    SharedWeatherIntervalCoverageResult,
)

DEFAULT_EVENT_WEATHER_DURATION = timedelta(hours=8)


@dataclass(slots=True)
class EnsureEventWeatherCoverageCommand:
    """Prepare shared Szolnok weather cache for one event window."""

    repository: EventRepository
    weather_coverage_command: EnsureSharedWeatherIntervalCoverageCommand

    def execute(self, *, event_id: uuid.UUID) -> SharedWeatherIntervalCoverageResult:
        event = self.repository.get_by_id(event_id)
        if event is None:
            raise EventNotFoundError(f"Event {event_id} was not found.")

        end_at = event.ends_at or event.starts_at + DEFAULT_EVENT_WEATHER_DURATION
        return self.weather_coverage_command.execute(
            start_at=event.starts_at,
            end_at=end_at,
        )


__all__ = ["EnsureEventWeatherCoverageCommand"]
