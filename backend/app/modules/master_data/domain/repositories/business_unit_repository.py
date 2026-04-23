"""Business unit repository contract."""

from __future__ import annotations

from typing import Protocol

from app.modules.master_data.domain.entities.business_unit import BusinessUnit


class BusinessUnitRepository(Protocol):
    """Defines business unit read access needed in the MVP."""

    def list_all(self, *, active_only: bool = True) -> list[BusinessUnit]:
        """Return business units ordered for UI consumption."""
