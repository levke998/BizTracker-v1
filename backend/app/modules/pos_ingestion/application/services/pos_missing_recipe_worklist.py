"""Read model for POS-created products that still need recipes."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session

from app.modules.master_data.infrastructure.orm.category_model import CategoryModel
from app.modules.master_data.infrastructure.orm.product_model import ProductModel
from app.modules.pos_ingestion.infrastructure.orm.pos_product_alias_model import (
    PosProductAliasModel,
)
from app.modules.production.infrastructure.orm.recipe_model import RecipeModel


@dataclass(frozen=True, slots=True)
class PosMissingRecipeWorklistItem:
    """One POS-origin product that has no active recipe yet."""

    product_id: uuid.UUID
    business_unit_id: uuid.UUID
    product_name: str
    category_name: str | None
    product_type: str
    sale_price_gross: Decimal | None
    sale_price_last_seen_at: datetime | None
    sale_price_source: str | None
    alias_count: int
    occurrence_count: int
    first_seen_at: datetime | None
    last_seen_at: datetime | None
    latest_source_product_name: str | None
    latest_source_system: str | None


class PosMissingRecipeWorklistService:
    """Build a non-blocking worklist for recipe coverage after POS imports."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def list_items(
        self,
        *,
        business_unit_id: uuid.UUID | None = None,
        limit: int = 100,
    ) -> list[PosMissingRecipeWorklistItem]:
        """Return POS-origin products without an active recipe."""

        latest_alias_subquery = (
            select(
                PosProductAliasModel.product_id.label("product_id"),
                PosProductAliasModel.source_product_name.label("source_product_name"),
                PosProductAliasModel.source_system.label("source_system"),
                func.row_number()
                .over(
                    partition_by=PosProductAliasModel.product_id,
                    order_by=(
                        PosProductAliasModel.last_seen_at.desc().nulls_last(),
                        PosProductAliasModel.updated_at.desc(),
                    ),
                )
                .label("row_no"),
            )
            .where(PosProductAliasModel.product_id.is_not(None))
            .subquery()
        )

        statement = (
            select(
                ProductModel.id,
                ProductModel.business_unit_id,
                ProductModel.name,
                CategoryModel.name,
                ProductModel.product_type,
                ProductModel.sale_price_gross,
                ProductModel.sale_price_last_seen_at,
                ProductModel.sale_price_source,
                func.count(PosProductAliasModel.id),
                func.coalesce(func.sum(PosProductAliasModel.occurrence_count), 0),
                func.min(PosProductAliasModel.first_seen_at),
                func.max(PosProductAliasModel.last_seen_at),
                latest_alias_subquery.c.source_product_name,
                latest_alias_subquery.c.source_system,
            )
            .join(
                PosProductAliasModel,
                PosProductAliasModel.product_id == ProductModel.id,
            )
            .outerjoin(CategoryModel, ProductModel.category_id == CategoryModel.id)
            .outerjoin(
                latest_alias_subquery,
                (latest_alias_subquery.c.product_id == ProductModel.id)
                & (latest_alias_subquery.c.row_no == 1),
            )
            .where(ProductModel.is_active.is_(True))
            .where(PosProductAliasModel.is_active.is_(True))
            .where(
                ~exists()
                .where(RecipeModel.product_id == ProductModel.id)
                .where(RecipeModel.is_active.is_(True))
            )
            .group_by(
                ProductModel.id,
                CategoryModel.name,
                latest_alias_subquery.c.source_product_name,
                latest_alias_subquery.c.source_system,
            )
            .order_by(
                func.max(PosProductAliasModel.last_seen_at).desc().nulls_last(),
                func.sum(PosProductAliasModel.occurrence_count).desc(),
                ProductModel.name.asc(),
            )
            .limit(limit)
        )
        if business_unit_id is not None:
            statement = statement.where(ProductModel.business_unit_id == business_unit_id)

        rows = self._session.execute(statement).all()
        return [
            PosMissingRecipeWorklistItem(
                product_id=product_id,
                business_unit_id=row_business_unit_id,
                product_name=product_name,
                category_name=category_name,
                product_type=product_type,
                sale_price_gross=sale_price_gross,
                sale_price_last_seen_at=sale_price_last_seen_at,
                sale_price_source=sale_price_source,
                alias_count=int(alias_count or 0),
                occurrence_count=int(occurrence_count or 0),
                first_seen_at=first_seen_at,
                last_seen_at=last_seen_at,
                latest_source_product_name=latest_source_product_name,
                latest_source_system=latest_source_system,
            )
            for (
                product_id,
                row_business_unit_id,
                product_name,
                category_name,
                product_type,
                sale_price_gross,
                sale_price_last_seen_at,
                sale_price_source,
                alias_count,
                occurrence_count,
                first_seen_at,
                last_seen_at,
                latest_source_product_name,
                latest_source_system,
            ) in rows
        ]
