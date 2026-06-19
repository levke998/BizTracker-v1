"""SQLAlchemy adapter for POS product alias review."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
import uuid

import sqlalchemy as sa
from sqlalchemy import case, cast, func, select
from sqlalchemy.orm import Session

from app.modules.imports.infrastructure.orm.import_batch_model import ImportBatchModel
from app.modules.imports.infrastructure.orm.import_row_model import ImportRowModel
from app.modules.master_data.infrastructure.orm.product_model import ProductModel
from app.modules.pos_ingestion.domain.entities.product_alias import (
    PosMappingReadiness,
    PosProductAlias,
)
from app.modules.pos_ingestion.infrastructure.orm.pos_product_alias_model import (
    PosProductAliasModel,
)


class SqlAlchemyPosProductAliasRepository:
    """Persist POS alias review state through SQLAlchemy."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def list_aliases(
        self,
        *,
        business_unit_id: uuid.UUID | None = None,
        status: str | None = None,
    ) -> list[PosProductAlias]:
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

        return [
            self._to_domain(model)
            for model in self._session.scalars(statement).all()
        ]

    def get_aliases(self, alias_ids: tuple[uuid.UUID, ...]) -> list[PosProductAlias]:
        if not alias_ids:
            return []

        models = self._session.scalars(
            select(PosProductAliasModel).where(PosProductAliasModel.id.in_(alias_ids))
        ).all()
        return [self._to_domain(model) for model in models]

    def product_belongs_to_business_unit(
        self,
        *,
        product_id: uuid.UUID,
        business_unit_id: uuid.UUID,
    ) -> bool:
        return (
            self._session.scalar(
                select(ProductModel.id)
                .where(ProductModel.id == product_id)
                .where(ProductModel.business_unit_id == business_unit_id)
            )
            is not None
        )

    def save_aliases(
        self,
        aliases: tuple[PosProductAlias, ...],
    ) -> list[PosProductAlias]:
        models_by_id = {
            model.id: model
            for model in self._session.scalars(
                select(PosProductAliasModel).where(
                    PosProductAliasModel.id.in_([alias.id for alias in aliases])
                )
            ).all()
        }

        for alias in aliases:
            model = models_by_id[alias.id]
            model.product_id = alias.product_id
            model.status = alias.status
            model.mapping_confidence = alias.mapping_confidence
            model.notes = alias.notes
            model.is_active = alias.is_active

        self._session.commit()
        for model in models_by_id.values():
            self._session.refresh(model)

        return [
            self._to_domain(models_by_id[alias.id])
            for alias in aliases
        ]

    def get_mapping_readiness(
        self,
        *,
        business_unit_id: uuid.UUID | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> PosMappingReadiness:
        payload = ImportRowModel.normalized_payload
        product_name = func.trim(payload["product_name"].as_string())
        source_product_id = func.coalesce(
            func.nullif(func.trim(payload["source_product_id"].as_string()), ""),
            func.nullif(func.trim(payload["pos_product_id"].as_string()), ""),
        )
        source_sku = func.nullif(func.trim(payload["sku"].as_string()), "")
        source_barcode = func.nullif(func.trim(payload["barcode"].as_string()), "")
        source_product_key = case(
            (
                source_product_id.is_not(None),
                func.concat("id:", func.lower(source_product_id)),
            ),
            (
                source_sku.is_not(None),
                func.concat("sku:", func.lower(source_sku)),
            ),
            (
                source_barcode.is_not(None),
                func.concat("barcode:", func.lower(source_barcode)),
            ),
            else_=func.concat("name:", func.lower(product_name)),
        )
        occurred_date = cast(
            func.coalesce(
                payload["occurred_at"].as_string(),
                payload["date"].as_string(),
            ),
            sa.Date,
        )
        gross_amount = cast(
            func.coalesce(payload["gross_amount"].as_string(), "0"),
            sa.Numeric(18, 2),
        )

        statement = (
            select(
                source_product_key.label("source_product_key"),
                PosProductAliasModel.id.label("alias_id"),
                PosProductAliasModel.status.label("alias_status"),
                func.count(ImportRowModel.id).label("row_count"),
                func.coalesce(func.sum(gross_amount), 0).label("gross_revenue"),
            )
            .join(
                ImportBatchModel,
                ImportBatchModel.id == ImportRowModel.batch_id,
            )
            .outerjoin(
                PosProductAliasModel,
                sa.and_(
                    PosProductAliasModel.business_unit_id
                    == ImportBatchModel.business_unit_id,
                    PosProductAliasModel.source_system == ImportBatchModel.import_type,
                    PosProductAliasModel.source_product_key == source_product_key,
                    PosProductAliasModel.is_active.is_(True),
                ),
            )
            .where(ImportRowModel.parse_status == "parsed")
            .where(
                ImportBatchModel.import_type.in_(
                    ("pos_sales", "gourmand_pos_sales", "flow_pos_sales")
                )
            )
            .where(product_name.is_not(None))
            .group_by(
                source_product_key,
                PosProductAliasModel.id,
                PosProductAliasModel.status,
            )
        )
        if business_unit_id is not None:
            statement = statement.where(
                ImportBatchModel.business_unit_id == business_unit_id
            )
        if start_date is not None:
            statement = statement.where(occurred_date >= start_date)
        if end_date is not None:
            statement = statement.where(occurred_date <= end_date)

        rows = self._session.execute(statement).all()
        total_alias_count = len(rows)
        mapped_alias_count = sum(1 for row in rows if row.alias_status == "mapped")
        automatic_alias_count = sum(
            1
            for row in rows
            if row.alias_id is not None and row.alias_status != "mapped"
        )
        missing_alias_count = sum(1 for row in rows if row.alias_id is None)
        total_row_count = sum(int(row.row_count) for row in rows)
        mapped_row_count = sum(
            int(row.row_count) for row in rows if row.alias_status == "mapped"
        )
        automatic_row_count = sum(
            int(row.row_count)
            for row in rows
            if row.alias_id is not None and row.alias_status != "mapped"
        )
        missing_row_count = sum(
            int(row.row_count) for row in rows if row.alias_id is None
        )
        total_gross_revenue = sum(
            (Decimal(row.gross_revenue) for row in rows),
            Decimal("0"),
        )
        mapped_gross_revenue = sum(
            (
                Decimal(row.gross_revenue)
                for row in rows
                if row.alias_status == "mapped"
            ),
            Decimal("0"),
        )
        automatic_gross_revenue = sum(
            (
                Decimal(row.gross_revenue)
                for row in rows
                if row.alias_id is not None and row.alias_status != "mapped"
            ),
            Decimal("0"),
        )
        missing_gross_revenue = sum(
            (
                Decimal(row.gross_revenue)
                for row in rows
                if row.alias_id is None
            ),
            Decimal("0"),
        )

        return PosMappingReadiness(
            status=_readiness_status(
                total_row_count=total_row_count,
                mapped_row_count=mapped_row_count,
            ),
            alias_coverage_percent=_coverage_percent(
                mapped_alias_count,
                total_alias_count,
            ),
            row_coverage_percent=_coverage_percent(
                mapped_row_count,
                total_row_count,
            ),
            gross_revenue_coverage_percent=_coverage_percent(
                mapped_gross_revenue,
                total_gross_revenue,
            ),
            total_alias_count=total_alias_count,
            mapped_alias_count=mapped_alias_count,
            automatic_alias_count=automatic_alias_count,
            missing_alias_count=missing_alias_count,
            total_row_count=total_row_count,
            mapped_row_count=mapped_row_count,
            automatic_row_count=automatic_row_count,
            missing_row_count=missing_row_count,
            total_gross_revenue=total_gross_revenue,
            mapped_gross_revenue=mapped_gross_revenue,
            automatic_gross_revenue=automatic_gross_revenue,
            missing_gross_revenue=missing_gross_revenue,
        )

    @staticmethod
    def _to_domain(model: PosProductAliasModel) -> PosProductAlias:
        return PosProductAlias(
            id=model.id,
            business_unit_id=model.business_unit_id,
            product_id=model.product_id,
            source_system=model.source_system,
            source_product_key=model.source_product_key,
            source_product_name=model.source_product_name,
            source_sku=model.source_sku,
            source_barcode=model.source_barcode,
            status=model.status,
            mapping_confidence=model.mapping_confidence,
            occurrence_count=model.occurrence_count,
            first_seen_at=model.first_seen_at,
            last_seen_at=model.last_seen_at,
            last_import_batch_id=model.last_import_batch_id,
            last_import_row_id=model.last_import_row_id,
            notes=model.notes,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


def _coverage_percent(
    covered: int | Decimal,
    total: int | Decimal,
) -> Decimal:
    if total == 0:
        return Decimal("0")
    return (Decimal(covered) * Decimal("100") / Decimal(total)).quantize(
        Decimal("0.01")
    )


def _readiness_status(*, total_row_count: int, mapped_row_count: int) -> str:
    if total_row_count == 0:
        return "no_data"
    if mapped_row_count == total_row_count:
        return "complete"
    if mapped_row_count > 0:
        return "partial"
    return "missing"
