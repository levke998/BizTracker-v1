"""Repository contract for POS product alias review."""

from __future__ import annotations

from typing import Protocol
from datetime import date
import uuid

from app.modules.pos_ingestion.domain.entities.product_alias import (
    PosMappingReadiness,
    PosProductAlias,
)


class PosProductAliasRepository(Protocol):
    """Persistence boundary used by POS alias review use cases."""

    def list_aliases(
        self,
        *,
        business_unit_id: uuid.UUID | None = None,
        status: str | None = None,
    ) -> list[PosProductAlias]:
        """Return aliases ordered for review."""

    def get_aliases(self, alias_ids: tuple[uuid.UUID, ...]) -> list[PosProductAlias]:
        """Return aliases matching the requested identifiers."""

    def product_belongs_to_business_unit(
        self,
        *,
        product_id: uuid.UUID,
        business_unit_id: uuid.UUID,
    ) -> bool:
        """Return whether the product is valid for the alias business unit."""

    def save_aliases(
        self,
        aliases: tuple[PosProductAlias, ...],
    ) -> list[PosProductAlias]:
        """Persist reviewed aliases in one transaction and return refreshed rows."""

    def get_mapping_readiness(
        self,
        *,
        business_unit_id: uuid.UUID | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> PosMappingReadiness:
        """Return traffic-weighted POS mapping readiness."""
