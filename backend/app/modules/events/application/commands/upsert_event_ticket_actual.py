"""Upsert event ticket actual command."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.modules.events.application.commands.create_event import EventNotFoundError
from app.modules.events.domain.entities.event_ticket_actual import (
    EventTicketActual,
    NewEventTicketActual,
)
from app.modules.events.domain.repositories.event_ticket_actual_repository import (
    EventTicketActualRepository,
)


class EventTicketActualValidationError(ValueError):
    """Raised when ticket actual input is invalid."""


@dataclass(slots=True)
class UpsertEventTicketActualCommand:
    """Create or update ticket-system actuals for one event."""

    repository: EventTicketActualRepository

    def execute(
        self,
        *,
        event_id: uuid.UUID,
        source_name: str | None = None,
        source_reference: str | None = None,
        sold_quantity: Decimal = Decimal("0"),
        gross_revenue: Decimal = Decimal("0"),
        net_revenue: Decimal | None = None,
        vat_amount: Decimal | None = None,
        vat_rate_id: uuid.UUID | None = None,
        platform_fee_gross: Decimal = Decimal("0"),
        reported_at: datetime | None = None,
        notes: str | None = None,
    ) -> EventTicketActual:
        if not self.repository.event_exists(event_id):
            raise EventNotFoundError(f"Event {event_id} was not found.")
        if vat_rate_id is not None and not self.repository.vat_rate_exists(vat_rate_id):
            raise EventTicketActualValidationError(f"VAT rate {vat_rate_id} was not found.")
        if sold_quantity < 0:
            raise EventTicketActualValidationError("Sold quantity cannot be negative.")
        if gross_revenue < 0 or platform_fee_gross < 0:
            raise EventTicketActualValidationError("Ticket amounts cannot be negative.")
        if net_revenue is not None and net_revenue < 0:
            raise EventTicketActualValidationError("Net revenue cannot be negative.")
        if vat_amount is not None and vat_amount < 0:
            raise EventTicketActualValidationError("VAT amount cannot be negative.")

        return self.repository.upsert(
            NewEventTicketActual(
                event_id=event_id,
                source_name=self._clean_text(source_name),
                source_reference=self._clean_text(source_reference),
                sold_quantity=sold_quantity,
                gross_revenue=gross_revenue,
                net_revenue=net_revenue,
                vat_amount=vat_amount,
                vat_rate_id=vat_rate_id,
                platform_fee_gross=platform_fee_gross,
                reported_at=reported_at,
                notes=self._clean_text(notes),
            )
        )

    @staticmethod
    def _clean_text(value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None
