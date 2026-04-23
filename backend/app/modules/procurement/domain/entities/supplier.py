"""Procurement supplier domain entities."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Supplier:
    """Represents one supplier read model."""

    id: uuid.UUID
    business_unit_id: uuid.UUID
    name: str
    tax_id: str | None
    contact_name: str | None
    email: str | None
    phone: str | None
    notes: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class NewSupplier:
    """Draft supplier before persistence."""

    business_unit_id: uuid.UUID
    name: str
    tax_id: str | None
    contact_name: str | None
    email: str | None
    phone: str | None
    notes: str | None
    is_active: bool
