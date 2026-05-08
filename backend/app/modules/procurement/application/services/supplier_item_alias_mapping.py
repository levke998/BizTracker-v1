"""Application service for supplier item alias review and approval."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.inventory.infrastructure.orm.inventory_item_model import (
    InventoryItemModel,
)
from app.modules.procurement.infrastructure.orm.supplier_item_alias_model import (
    SupplierItemAliasModel,
)


class SupplierItemAliasNotFoundError(Exception):
    """Raised when the requested supplier item alias does not exist."""


class SupplierItemAliasInventoryItemMismatchError(Exception):
    """Raised when the selected inventory item cannot be used for the alias."""


class SupplierItemAliasMappingService:
    """Coordinates supplier item alias review operations."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def list_aliases(
        self,
        *,
        business_unit_id: uuid.UUID | None = None,
        supplier_id: uuid.UUID | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[SupplierItemAliasModel]:
        """Return supplier item aliases ordered for review screens."""

        statement = select(SupplierItemAliasModel).order_by(
            SupplierItemAliasModel.status.asc(),
            SupplierItemAliasModel.last_seen_at.desc(),
            SupplierItemAliasModel.source_item_name.asc(),
        )
        if business_unit_id is not None:
            statement = statement.where(
                SupplierItemAliasModel.business_unit_id == business_unit_id
            )
        if supplier_id is not None:
            statement = statement.where(SupplierItemAliasModel.supplier_id == supplier_id)
        if status is not None:
            statement = statement.where(SupplierItemAliasModel.status == status)

        return list(self._session.scalars(statement.limit(limit)).all())

    def approve_mapping(
        self,
        *,
        alias_id: uuid.UUID,
        inventory_item_id: uuid.UUID,
        internal_display_name: str | None = None,
        notes: str | None = None,
    ) -> SupplierItemAliasModel:
        """Approve one supplier source item against an internal inventory item."""

        alias = self._session.get(SupplierItemAliasModel, alias_id)
        if alias is None:
            raise SupplierItemAliasNotFoundError(
                f"Supplier item alias {alias_id} was not found."
            )

        inventory_item = self._session.get(InventoryItemModel, inventory_item_id)
        if (
            inventory_item is None
            or inventory_item.business_unit_id != alias.business_unit_id
        ):
            raise SupplierItemAliasInventoryItemMismatchError(
                "The selected inventory item does not belong to the alias business unit."
            )

        alias.inventory_item_id = inventory_item.id
        alias.internal_display_name = (
            internal_display_name.strip() if internal_display_name else inventory_item.name
        )
        alias.status = "mapped"
        alias.mapping_confidence = "manual"
        alias.notes = notes.strip() if notes else None
        self._session.commit()
        self._session.refresh(alias)
        return alias
