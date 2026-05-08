"""Create/update event use cases."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.modules.events.domain.entities.event import Event, NewEvent
from app.modules.events.domain.repositories.event_repository import EventRepository

EVENT_STATUSES = {"planned", "confirmed", "completed", "cancelled"}


class EventBusinessUnitNotFoundError(Exception):
    """Raised when the selected business unit does not exist."""


class EventLocationMismatchError(Exception):
    """Raised when the selected location does not belong to the business unit."""


class EventValidationError(Exception):
    """Raised when event business rules are violated."""


class EventNotFoundError(Exception):
    """Raised when an event does not exist."""


def _normalize_event(
    *,
    business_unit_id: uuid.UUID,
    location_id: uuid.UUID | None,
    title: str,
    status: str,
    starts_at: datetime,
    ends_at: datetime | None,
    performer_name: str | None,
    expected_attendance: int | None,
    ticket_revenue_gross: Decimal,
    bar_revenue_gross: Decimal,
    performer_share_percent: Decimal,
    performer_fixed_fee: Decimal,
    event_cost_amount: Decimal,
    notes: str | None,
    is_active: bool,
) -> NewEvent:
    normalized_title = title.strip()
    normalized_status = status.strip().lower()

    if normalized_status not in EVENT_STATUSES:
        raise EventValidationError("Unsupported event status.")
    if ends_at is not None and ends_at <= starts_at:
        raise EventValidationError("Event end must be after event start.")
    if not normalized_title:
        raise EventValidationError("Event title is required.")
    if expected_attendance is not None and expected_attendance < 0:
        raise EventValidationError("Expected attendance cannot be negative.")
    if performer_share_percent < 0 or performer_share_percent > 100:
        raise EventValidationError("Performer share percent must be between 0 and 100.")
    for amount in (
        ticket_revenue_gross,
        bar_revenue_gross,
        performer_fixed_fee,
        event_cost_amount,
    ):
        if amount < 0:
            raise EventValidationError("Event amounts cannot be negative.")

    return NewEvent(
        business_unit_id=business_unit_id,
        location_id=location_id,
        title=normalized_title,
        status=normalized_status,
        starts_at=starts_at,
        ends_at=ends_at,
        performer_name=performer_name.strip() if performer_name else None,
        expected_attendance=expected_attendance,
        ticket_revenue_gross=ticket_revenue_gross,
        bar_revenue_gross=bar_revenue_gross,
        performer_share_percent=performer_share_percent,
        performer_fixed_fee=performer_fixed_fee,
        event_cost_amount=event_cost_amount,
        notes=notes.strip() if notes else None,
        is_active=is_active,
    )


@dataclass(slots=True)
class CreateEventCommand:
    """Create one Flow/event planning record."""

    repository: EventRepository

    def execute(
        self,
        *,
        business_unit_id: uuid.UUID,
        location_id: uuid.UUID | None,
        title: str,
        status: str,
        starts_at: datetime,
        ends_at: datetime | None = None,
        performer_name: str | None = None,
        expected_attendance: int | None = None,
        ticket_revenue_gross: Decimal = Decimal("0"),
        bar_revenue_gross: Decimal = Decimal("0"),
        performer_share_percent: Decimal = Decimal("80"),
        performer_fixed_fee: Decimal = Decimal("0"),
        event_cost_amount: Decimal = Decimal("0"),
        notes: str | None = None,
        is_active: bool = True,
    ) -> Event:
        if not self.repository.business_unit_exists(business_unit_id):
            raise EventBusinessUnitNotFoundError(
                f"Business unit {business_unit_id} was not found."
            )
        if location_id is not None and not self.repository.location_belongs_to_business_unit(
            location_id=location_id,
            business_unit_id=business_unit_id,
        ):
            raise EventLocationMismatchError(
                "The selected location does not belong to the event business unit."
            )

        event = _normalize_event(
            business_unit_id=business_unit_id,
            location_id=location_id,
            title=title,
            status=status,
            starts_at=starts_at,
            ends_at=ends_at,
            performer_name=performer_name,
            expected_attendance=expected_attendance,
            ticket_revenue_gross=ticket_revenue_gross,
            bar_revenue_gross=bar_revenue_gross,
            performer_share_percent=performer_share_percent,
            performer_fixed_fee=performer_fixed_fee,
            event_cost_amount=event_cost_amount,
            notes=notes,
            is_active=is_active,
        )
        return self.repository.create(event)


@dataclass(slots=True)
class UpdateEventCommand:
    """Update one event planning record."""

    repository: EventRepository

    def execute(self, event_id: uuid.UUID, **payload: object) -> Event:
        business_unit_id = payload["business_unit_id"]
        location_id = payload["location_id"]

        if not isinstance(business_unit_id, uuid.UUID):
            raise EventValidationError("Business unit is required.")
        if location_id is not None and not isinstance(location_id, uuid.UUID):
            raise EventValidationError("Location id is invalid.")
        if not self.repository.business_unit_exists(business_unit_id):
            raise EventBusinessUnitNotFoundError(
                f"Business unit {business_unit_id} was not found."
            )
        if location_id is not None and not self.repository.location_belongs_to_business_unit(
            location_id=location_id,
            business_unit_id=business_unit_id,
        ):
            raise EventLocationMismatchError(
                "The selected location does not belong to the event business unit."
            )

        event = _normalize_event(**payload)  # type: ignore[arg-type]
        updated = self.repository.update(event_id, event)
        if updated is None:
            raise EventNotFoundError(f"Event {event_id} was not found.")
        return updated


@dataclass(slots=True)
class ArchiveEventCommand:
    """Archive one event planning record."""

    repository: EventRepository

    def execute(self, event_id: uuid.UUID) -> Event:
        event = self.repository.archive(event_id)
        if event is None:
            raise EventNotFoundError(f"Event {event_id} was not found.")
        return event
