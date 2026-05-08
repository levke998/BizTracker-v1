"""Get event ticket actual query."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.modules.events.application.commands.create_event import EventNotFoundError
from app.modules.events.domain.entities.event_ticket_actual import EventTicketActual
from app.modules.events.domain.repositories.event_ticket_actual_repository import (
    EventTicketActualRepository,
)


@dataclass(slots=True)
class GetEventTicketActualQuery:
    """Return ticket-system actuals for one event."""

    repository: EventTicketActualRepository

    def execute(self, *, event_id: uuid.UUID) -> EventTicketActual | None:
        if not self.repository.event_exists(event_id):
            raise EventNotFoundError(f"Event {event_id} was not found.")
        return self.repository.get_by_event_id(event_id)
