"""List events query."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from app.modules.events.domain.entities.event import Event
from app.modules.events.domain.repositories.event_repository import EventRepository


@dataclass(slots=True)
class ListEventsQuery:
    """Return event planning records with lightweight filters."""

    repository: EventRepository

    def execute(
        self,
        *,
        business_unit_id: uuid.UUID | None = None,
        status: str | None = None,
        is_active: bool | None = None,
        starts_from: datetime | None = None,
        starts_to: datetime | None = None,
        limit: int = 50,
    ) -> list[Event]:
        return self.repository.list_many(
            business_unit_id=business_unit_id,
            status=status,
            is_active=is_active,
            starts_from=starts_from,
            starts_to=starts_to,
            limit=limit,
        )
