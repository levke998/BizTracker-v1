"""Event cost line repository contract."""

from __future__ import annotations

import uuid
from typing import Protocol

from app.modules.events.domain.entities.event_cost import EventCostLine, NewEventCostLine


class EventCostRepository(Protocol):
    """Defines persistence for event cost lines."""

    def list_by_event_id(self, event_id: uuid.UUID) -> list[EventCostLine]:
        """Return cost lines attached to one event."""

    def replace_for_event(
        self,
        *,
        event_id: uuid.UUID,
        cost_lines: list[NewEventCostLine],
    ) -> list[EventCostLine]:
        """Replace all manual cost lines for one event."""

    def event_exists(self, event_id: uuid.UUID) -> bool:
        """Return whether the event exists."""
