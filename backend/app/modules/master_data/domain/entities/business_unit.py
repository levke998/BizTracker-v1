"""Business unit domain entity."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class BusinessUnit:
    """Represents a top-level business unit."""

    id: uuid.UUID
    code: str
    name: str
    type: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
