"""Location repository contract."""

from __future__ import annotations

import uuid
from typing import Protocol

from app.modules.master_data.domain.entities.location import Location


class LocationRepository(Protocol):
    """Defines location read access needed in the MVP."""

    def list_by_business_unit(
        self,
        business_unit_id: uuid.UUID,
        *,
        active_only: bool = True,
    ) -> list[Location]:
        """Return locations for a business unit."""
