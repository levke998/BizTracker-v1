"""Event ticket actual repository contract."""

from __future__ import annotations

import uuid
from typing import Protocol

from app.modules.events.domain.entities.event_ticket_actual import (
    EventTicketActual,
    NewEventTicketActual,
)


class EventTicketActualRepository(Protocol):
    """Defines persistence for event ticket-system actuals."""

    def get_by_event_id(self, event_id: uuid.UUID) -> EventTicketActual | None:
        """Return ticket actuals for one event, if present."""

    def upsert(self, actual: NewEventTicketActual) -> EventTicketActual:
        """Create or update ticket actuals for one event."""

    def event_exists(self, event_id: uuid.UUID) -> bool:
        """Return whether the event exists."""

    def vat_rate_exists(self, vat_rate_id: uuid.UUID) -> bool:
        """Return whether the VAT rate exists."""
