"""Replace event cost lines command."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.modules.events.application.commands.create_event import EventNotFoundError
from app.modules.events.domain.entities.event_cost import EventCostLine, NewEventCostLine
from app.modules.events.domain.repositories.event_cost_repository import EventCostRepository


class EventCostLineValidationError(ValueError):
    """Raised when event cost line input is invalid."""


@dataclass(frozen=True, slots=True)
class EventCostLineInput:
    """Validated input shape for one event cost line."""

    category: str
    description: str
    amount_gross: Decimal
    source_type: str = "manual"
    source_reference: str | None = None
    incurred_at: datetime | None = None
    notes: str | None = None


@dataclass(slots=True)
class ReplaceEventCostLinesCommand:
    """Replace all cost lines attached to one event."""

    repository: EventCostRepository

    def execute(
        self,
        *,
        event_id: uuid.UUID,
        cost_lines: list[EventCostLineInput],
    ) -> list[EventCostLine]:
        if not self.repository.event_exists(event_id):
            raise EventNotFoundError(f"Event {event_id} was not found.")

        validated = [self._validate_line(event_id, line) for line in cost_lines]
        return self.repository.replace_for_event(
            event_id=event_id,
            cost_lines=validated,
        )

    def _validate_line(
        self,
        event_id: uuid.UUID,
        line: EventCostLineInput,
    ) -> NewEventCostLine:
        category = self._clean_text(line.category) or "egyeb"
        description = self._clean_text(line.description)
        source_type = self._clean_text(line.source_type) or "manual"

        if description is None:
            raise EventCostLineValidationError("Cost line description is required.")
        if line.amount_gross < 0:
            raise EventCostLineValidationError("Cost line amount cannot be negative.")

        return NewEventCostLine(
            event_id=event_id,
            category=category[:80],
            description=description[:240],
            amount_gross=line.amount_gross,
            source_type=source_type[:40],
            source_reference=self._clean_text(line.source_reference),
            incurred_at=line.incurred_at,
            notes=self._clean_text(line.notes),
        )

    @staticmethod
    def _clean_text(value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None
