"""List event cost lines query."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.modules.events.application.commands.create_event import EventNotFoundError
from app.modules.events.domain.entities.event_cost import EventCostLine
from app.modules.events.domain.repositories.event_cost_repository import EventCostRepository


@dataclass(slots=True)
class ListEventCostLinesQuery:
    """Return cost lines attached to one event."""

    repository: EventCostRepository

    def execute(self, event_id: uuid.UUID) -> list[EventCostLine]:
        if not self.repository.event_exists(event_id):
            raise EventNotFoundError(f"Event {event_id} was not found.")
        return self.repository.list_by_event_id(event_id)
