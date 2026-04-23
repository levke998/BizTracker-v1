"""Category domain entity."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Category:
    """Represents a business-unit-specific category."""

    id: uuid.UUID
    business_unit_id: uuid.UUID
    parent_id: uuid.UUID | None
    name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
