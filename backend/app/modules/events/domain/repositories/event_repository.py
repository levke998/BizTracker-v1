"""Event repository contract."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Protocol

from app.modules.events.domain.entities.event import Event, NewEvent


class EventRepository(Protocol):
    """Defines persistence access for event planning data."""

    def get_by_id(self, event_id: uuid.UUID) -> Event | None:
        """Return one event by id if it exists."""

    def list_many(
        self,
        *,
        business_unit_id: uuid.UUID | None = None,
        status: str | None = None,
        is_active: bool | None = None,
        starts_from: datetime | None = None,
        starts_to: datetime | None = None,
        limit: int = 50,
    ) -> list[Event]:
        """List events with lightweight filters."""

    def create(self, event: NewEvent) -> Event:
        """Create one event."""

    def update(self, event_id: uuid.UUID, event: NewEvent) -> Event | None:
        """Update one event if it exists."""

    def archive(self, event_id: uuid.UUID) -> Event | None:
        """Archive one event if it exists."""

    def business_unit_exists(self, business_unit_id: uuid.UUID) -> bool:
        """Return whether the referenced business unit exists."""

    def location_belongs_to_business_unit(
        self,
        *,
        location_id: uuid.UUID,
        business_unit_id: uuid.UUID,
    ) -> bool:
        """Return whether the location belongs to the selected business unit."""
