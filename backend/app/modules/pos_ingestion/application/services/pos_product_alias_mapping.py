"""Application service for POS product alias review and approval."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.master_data.infrastructure.orm.product_model import ProductModel
from app.modules.pos_ingestion.infrastructure.orm.pos_product_alias_model import (
    PosProductAliasModel,
)


class PosProductAliasNotFoundError(Exception):
    """Raised when the requested POS product alias does not exist."""


class PosProductAliasProductMismatchError(Exception):
    """Raised when the selected product cannot be used for the alias."""


class PosProductAliasMappingService:
    """Coordinates POS alias review operations."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def list_aliases(
        self,
        *,
        business_unit_id: uuid.UUID | None = None,
        status: str | None = None,
    ) -> list[PosProductAliasModel]:
        """Return aliases ordered for the review worklist."""

        statement = select(PosProductAliasModel).order_by(
            PosProductAliasModel.status.asc(),
            PosProductAliasModel.last_seen_at.desc().nulls_last(),
            PosProductAliasModel.source_product_name.asc(),
        )
        if business_unit_id is not None:
            statement = statement.where(
                PosProductAliasModel.business_unit_id == business_unit_id
            )
        if status is not None:
            statement = statement.where(PosProductAliasModel.status == status)

        return list(self._session.scalars(statement).all())

    def approve_mapping(
        self,
        *,
        alias_id: uuid.UUID,
        product_id: uuid.UUID,
        notes: str | None = None,
    ) -> PosProductAliasModel:
        """Approve one POS alias against one internal product."""

        alias = self._session.get(PosProductAliasModel, alias_id)
        if alias is None:
            raise PosProductAliasNotFoundError(
                f"POS product alias {alias_id} was not found."
            )

        product = self._session.get(ProductModel, product_id)
        if product is None or product.business_unit_id != alias.business_unit_id:
            raise PosProductAliasProductMismatchError(
                "The selected product does not belong to the alias business unit."
            )

        alias.product_id = product.id
        alias.status = "mapped"
        alias.mapping_confidence = "manual"
        alias.notes = notes.strip() if notes else None
        alias.is_active = True
        self._session.commit()
        self._session.refresh(alias)
        return alias
