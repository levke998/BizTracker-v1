"""Flow/event domain entities."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

MONEY_QUANT = Decimal("0.01")
PERFORMER_SETTLEMENT_TYPES = {"revenue_share", "fixed_fee", "hybrid"}


def _money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_QUANT)


def uses_revenue_share(settlement_type: str) -> bool:
    """Return whether performer compensation includes ticket revenue share."""

    return settlement_type in {"revenue_share", "hybrid"}


def uses_fixed_fee(settlement_type: str) -> bool:
    """Return whether performer compensation includes fixed fee."""

    return settlement_type in {"fixed_fee", "hybrid"}


@dataclass(frozen=True, slots=True)
class Event:
    """Represents one event planning and settlement-lite read model."""

    id: uuid.UUID
    business_unit_id: uuid.UUID
    location_id: uuid.UUID | None
    title: str
    status: str
    starts_at: datetime
    ends_at: datetime | None
    performer_name: str | None
    expected_attendance: int | None
    ticket_revenue_gross: Decimal
    bar_revenue_gross: Decimal
    performer_settlement_type: str
    performer_share_percent: Decimal
    performer_fixed_fee: Decimal
    event_cost_amount: Decimal
    notes: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @property
    def performer_share_amount(self) -> Decimal:
        """Return the configured revenue-share amount from ticket revenue."""

        if not uses_revenue_share(self.performer_settlement_type):
            return Decimal("0.00")
        return _money(self.ticket_revenue_gross * self.performer_share_percent / Decimal("100"))

    @property
    def performer_fixed_fee_amount(self) -> Decimal:
        """Return fixed performer fee if the settlement mode uses it."""

        if not uses_fixed_fee(self.performer_settlement_type):
            return Decimal("0.00")
        return _money(self.performer_fixed_fee)

    @property
    def performer_total_compensation_gross(self) -> Decimal:
        """Return total performer compensation used by settlement-lite."""

        return _money(self.performer_share_amount + self.performer_fixed_fee_amount)

    @property
    def retained_ticket_revenue(self) -> Decimal:
        """Return the ticket revenue retained by Flow after performer share."""

        return _money(self.ticket_revenue_gross - self.performer_share_amount)

    @property
    def own_revenue(self) -> Decimal:
        """Return retained ticket revenue plus bar revenue."""

        return _money(self.retained_ticket_revenue + self.bar_revenue_gross)

    @property
    def event_profit_lite(self) -> Decimal:
        """Return simplified event profit before deeper settlement rules."""

        return _money(self.own_revenue - self.performer_fixed_fee_amount - self.event_cost_amount)


@dataclass(frozen=True, slots=True)
class NewEvent:
    """Draft event before persistence."""

    business_unit_id: uuid.UUID
    location_id: uuid.UUID | None
    title: str
    status: str
    starts_at: datetime
    ends_at: datetime | None
    performer_name: str | None
    expected_attendance: int | None
    ticket_revenue_gross: Decimal
    bar_revenue_gross: Decimal
    performer_settlement_type: str
    performer_share_percent: Decimal
    performer_fixed_fee: Decimal
    event_cost_amount: Decimal
    notes: str | None
    is_active: bool
