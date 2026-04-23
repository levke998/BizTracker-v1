"""Unit of measure repository contract."""

from __future__ import annotations

from typing import Protocol

from app.modules.master_data.domain.entities.unit_of_measure import UnitOfMeasure


class UnitOfMeasureRepository(Protocol):
    """Defines unit-of-measure read access needed in the MVP."""

    def list_all(self) -> list[UnitOfMeasure]:
        """Return all available units of measure."""
