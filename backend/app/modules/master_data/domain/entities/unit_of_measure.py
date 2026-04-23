"""Unit of measure domain entity."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class UnitOfMeasure:
    """Represents a shared measurement unit."""

    id: uuid.UUID
    code: str
    name: str
    symbol: str | None
    created_at: datetime
    updated_at: datetime
