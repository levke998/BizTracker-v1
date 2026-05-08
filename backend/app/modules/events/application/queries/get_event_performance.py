"""Get event performance query."""

from __future__ import annotations

import uuid
from datetime import datetime

from app.modules.events.domain.entities.event_performance import EventPerformance
from app.modules.events.infrastructure.repositories.sqlalchemy_event_performance_repository import (
    SqlAlchemyEventPerformanceRepository,
)


class EventPerformanceNotFoundError(LookupError):
    """Raised when the requested event does not exist."""


class GetEventPerformanceQuery:
    """Return POS/weather performance for one planned event time window."""

    def __init__(self, repository: SqlAlchemyEventPerformanceRepository) -> None:
        self.repository = repository

    def execute(self, event_id: uuid.UUID) -> EventPerformance:
        performance = self.repository.get_by_event_id(event_id)
        if performance is None:
            raise EventPerformanceNotFoundError(f"Event {event_id} was not found.")
        return performance


class ListEventPerformancesQuery:
    """Return POS/weather performance rows for an event comparison view."""

    def __init__(self, repository: SqlAlchemyEventPerformanceRepository) -> None:
        self.repository = repository

    def execute(
        self,
        *,
        business_unit_id: uuid.UUID | None = None,
        status: str | None = None,
        is_active: bool | None = None,
        starts_from: datetime | None = None,
        starts_to: datetime | None = None,
        limit: int = 50,
    ) -> list[EventPerformance]:
        normalized_status = None if status in {None, "", "all"} else status
        return self.repository.list_many(
            business_unit_id=business_unit_id,
            status=normalized_status,
            is_active=is_active,
            starts_from=starts_from,
            starts_to=starts_to,
            limit=limit,
        )
