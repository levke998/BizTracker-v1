"""Location domain entity."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Location:
    """Represents a physical site belonging to a business unit."""

    id: uuid.UUID
    business_unit_id: uuid.UUID
    name: str
    kind: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
