"""Catalog synchronization for accepted POS import rows."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, time
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable, Mapping

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.imports.domain.entities.import_batch import NewImportRow
from app.modules.master_data.infrastructure.orm.category_model import CategoryModel
from app.modules.master_data.infrastructure.orm.product_model import ProductModel
from app.modules.master_data.infrastructure.orm.unit_of_measure_model import (
    UnitOfMeasureModel,
)
from app.modules.pos_ingestion.infrastructure.orm.pos_product_alias_model import (
    PosProductAliasModel,
)
from app.modules.production.infrastructure.orm.recipe_model import RecipeModel

AliasCacheKey = tuple[uuid.UUID, str, str]


class PosSaleCatalogSyncService:
    """Create or update category/product master data from POS rows."""

    default_currency = "HUF"

    def __init__(self, session: Session) -> None:
        self._session = session

    def sync_new_rows(
        self,
        *,
        business_unit_id: uuid.UUID,
        rows: Iterable[NewImportRow],
        source_system: str = "pos_sales",
        batch_id: uuid.UUID | None = None,
    ) -> None:
        pcs_uom = self._get_unit_of_measure("pcs")
        alias_cache: dict[AliasCacheKey, PosProductAliasModel] = {}
        for row in rows:
            if row.parse_status != "parsed" or row.normalized_payload is None:
                continue
            self._sync_payload(
                business_unit_id=business_unit_id,
                payload=row.normalized_payload,
                default_sales_uom_id=pcs_uom.id if pcs_uom is not None else None,
                source_system=source_system,
                batch_id=batch_id,
                alias_cache=alias_cache,
            )

    def _sync_payload(
        self,
        *,
        business_unit_id: uuid.UUID,
        payload: Mapping[str, Any],
        default_sales_uom_id: uuid.UUID | None,
        source_system: str,
        batch_id: uuid.UUID | None,
        alias_cache: dict[AliasCacheKey, PosProductAliasModel],
    ) -> None:
        product_name = _clean_text(payload.get("product_name"))
        if product_name is None:
            return

        category = self._get_or_create_category(
            business_unit_id=business_unit_id,
            category_name=_clean_text(payload.get("category_name")),
        )
        sale_price = self._extract_sale_price(payload)
        seen_at = _extract_seen_at(payload)
        mapped_alias = self._find_alias(
            business_unit_id=business_unit_id,
            payload=payload,
            source_system=source_system,
            source_product_name=product_name,
            alias_cache=alias_cache,
        )
        product = self._product_from_mapped_alias(
            alias=mapped_alias,
            business_unit_id=business_unit_id,
        )
        products: list[ProductModel] = []
        if product is None:
            products = self._find_products(
                business_unit_id=business_unit_id,
                product_name=product_name,
            )
            product = self._choose_primary_product(products)

        if product is None:
            product = ProductModel(
                business_unit_id=business_unit_id,
                category_id=category.id if category is not None else None,
                sales_uom_id=default_sales_uom_id,
                sku=_clean_text(payload.get("sku")),
                name=product_name,
                product_type=_infer_product_type(category.name if category else None),
                sale_price_gross=sale_price,
                sale_price_last_seen_at=seen_at if sale_price is not None else None,
                sale_price_source=source_system if sale_price is not None else None,
                default_unit_cost=None,
                currency=self.default_currency,
                is_active=True,
            )
            self._session.add(product)
            self._session.flush()
            self._upsert_alias(
                business_unit_id=business_unit_id,
                product=product,
                payload=payload,
                source_system=source_system,
                batch_id=batch_id,
                status="auto_created",
                mapping_confidence="name_auto",
                alias_cache=alias_cache,
            )
            return

        if products:
            self._archive_duplicate_products(
                products=products,
                primary_product_id=product.id,
            )
        if category is not None:
            product.category_id = category.id
        if self._should_update_sale_price(product=product, seen_at=seen_at, sale_price=sale_price):
            product.sale_price_gross = sale_price
            product.sale_price_last_seen_at = seen_at
            product.sale_price_source = source_system
        if default_sales_uom_id is not None and product.sales_uom_id is None:
            product.sales_uom_id = default_sales_uom_id
        product.product_type = _infer_product_type(
            category.name if category else None,
            fallback=product.product_type,
        )
        product.is_active = True
        self._upsert_alias(
            business_unit_id=business_unit_id,
            product=product,
            payload=payload,
            source_system=source_system,
            batch_id=batch_id,
            status="auto_created",
            mapping_confidence=_mapping_confidence(payload=payload, product=product),
            alias_cache=alias_cache,
        )

    def _upsert_alias(
        self,
        *,
        business_unit_id: uuid.UUID,
        product: ProductModel,
        payload: Mapping[str, Any],
        source_system: str,
        batch_id: uuid.UUID | None,
        status: str,
        mapping_confidence: str,
        alias_cache: dict[AliasCacheKey, PosProductAliasModel],
    ) -> None:
        source_product_name = _clean_text(payload.get("product_name"))
        if source_product_name is None:
            return

        source_product_key = _source_product_key(payload, source_product_name)
        cache_key = (business_unit_id, source_system, source_product_key)
        source_sku = _clean_text(payload.get("sku"))
        source_barcode = _clean_text(payload.get("barcode"))
        seen_at = _extract_seen_at(payload)

        alias = alias_cache.get(cache_key)
        if alias is None:
            with self._session.no_autoflush:
                alias = self._session.scalar(
                    select(PosProductAliasModel)
                    .where(PosProductAliasModel.business_unit_id == business_unit_id)
                    .where(PosProductAliasModel.source_system == source_system)
                    .where(PosProductAliasModel.source_product_key == source_product_key)
                    .limit(1)
                )
        if alias is None:
            alias = PosProductAliasModel(
                business_unit_id=business_unit_id,
                product_id=product.id,
                source_system=source_system,
                source_product_key=source_product_key,
                source_product_name=source_product_name,
                source_sku=source_sku,
                source_barcode=source_barcode,
                status=status,
                mapping_confidence=mapping_confidence,
                occurrence_count=1,
                first_seen_at=seen_at,
                last_seen_at=seen_at,
                last_import_batch_id=batch_id,
                last_import_row_id=None,
                is_active=True,
            )
            self._session.add(alias)
            alias_cache[cache_key] = alias
            return

        alias_cache[cache_key] = alias
        alias.source_product_name = source_product_name
        alias.source_sku = source_sku
        alias.source_barcode = source_barcode
        alias.occurrence_count += 1
        alias.first_seen_at = _earlier_datetime(alias.first_seen_at, seen_at)
        alias.last_seen_at = _later_datetime(alias.last_seen_at, seen_at)
        alias.last_import_batch_id = batch_id
        alias.is_active = True
        if alias.status == "mapped":
            return
        if alias.product_id is None or alias.status == "auto_created":
            alias.product_id = product.id
            alias.mapping_confidence = mapping_confidence
        alias.status = status

    def _find_alias(
        self,
        *,
        business_unit_id: uuid.UUID,
        payload: Mapping[str, Any],
        source_system: str,
        source_product_name: str,
        alias_cache: dict[AliasCacheKey, PosProductAliasModel],
    ) -> PosProductAliasModel | None:
        source_product_key = _source_product_key(payload, source_product_name)
        cache_key = (business_unit_id, source_system, source_product_key)
        alias = alias_cache.get(cache_key)
        if alias is not None:
            return alias

        with self._session.no_autoflush:
            alias = self._session.scalar(
                select(PosProductAliasModel)
                .where(PosProductAliasModel.business_unit_id == business_unit_id)
                .where(PosProductAliasModel.source_system == source_system)
                .where(PosProductAliasModel.source_product_key == source_product_key)
                .limit(1)
            )
        if alias is not None:
            alias_cache[cache_key] = alias
        return alias

    def _product_from_mapped_alias(
        self,
        *,
        alias: PosProductAliasModel | None,
        business_unit_id: uuid.UUID,
    ) -> ProductModel | None:
        if alias is None or alias.status != "mapped" or alias.product_id is None:
            return None

        product = self._session.get(ProductModel, alias.product_id)
        if product is None or product.business_unit_id != business_unit_id:
            return None
        return product

    def _get_or_create_category(
        self,
        *,
        business_unit_id: uuid.UUID,
        category_name: str | None,
    ) -> CategoryModel | None:
        if category_name is None:
            return None

        category = self._session.scalar(
            select(CategoryModel)
            .where(CategoryModel.business_unit_id == business_unit_id)
            .where(func.lower(CategoryModel.name) == category_name.lower())
            .order_by(CategoryModel.is_active.desc(), CategoryModel.created_at.asc())
            .limit(1)
        )
        if category is not None:
            category.name = category_name
            category.is_active = True
            return category

        category = CategoryModel(
            business_unit_id=business_unit_id,
            parent_id=None,
            name=category_name,
            is_active=True,
        )
        self._session.add(category)
        self._session.flush()
        return category

    def _find_products(
        self,
        *,
        business_unit_id: uuid.UUID,
        product_name: str,
    ) -> list[ProductModel]:
        return list(self._session.scalars(
            select(ProductModel)
            .where(ProductModel.business_unit_id == business_unit_id)
            .where(func.lower(ProductModel.name) == product_name.lower())
            .order_by(ProductModel.is_active.desc(), ProductModel.created_at.asc())
        ).all())

    def _choose_primary_product(self, products: list[ProductModel]) -> ProductModel | None:
        if not products:
            return None

        recipe_product_ids = {
            product_id
            for product_id, in self._session.execute(
                select(RecipeModel.product_id)
                .where(RecipeModel.product_id.in_([product.id for product in products]))
                .where(RecipeModel.is_active.is_(True))
            ).all()
        }
        return sorted(
            products,
            key=lambda product: (
                product.id not in recipe_product_ids,
                not product.is_active,
                product.created_at,
            ),
        )[0]

    @staticmethod
    def _archive_duplicate_products(
        *,
        products: list[ProductModel],
        primary_product_id: uuid.UUID,
    ) -> None:
        for product in products:
            if product.id != primary_product_id:
                product.is_active = False

    def _get_unit_of_measure(self, code: str) -> UnitOfMeasureModel | None:
        return self._session.scalar(
            select(UnitOfMeasureModel)
            .where(UnitOfMeasureModel.code == code)
            .limit(1)
        )

    @staticmethod
    def _extract_sale_price(payload: Mapping[str, Any]) -> Decimal | None:
        for key in ("unit_price", "sale_price_gross"):
            value = payload.get(key)
            if value is None:
                continue
            try:
                parsed = Decimal(str(value))
            except (InvalidOperation, ValueError):
                continue
            if parsed > 0:
                return parsed.quantize(Decimal("0.01"))

        gross_amount = payload.get("gross_amount")
        quantity = payload.get("quantity")
        try:
            gross = Decimal(str(gross_amount))
            qty = Decimal(str(quantity))
        except (InvalidOperation, ValueError):
            return None
        if gross <= 0 or qty <= 0:
            return None
        return (gross / qty).quantize(Decimal("0.01"))

    @staticmethod
    def _should_update_sale_price(
        *,
        product: ProductModel,
        seen_at: datetime | None,
        sale_price: Decimal | None,
    ) -> bool:
        if sale_price is None:
            return False

        current_seen_at = product.sale_price_last_seen_at
        if current_seen_at is None:
            return True
        if seen_at is None:
            return False

        if current_seen_at.tzinfo is None:
            current_seen_at = current_seen_at.replace(tzinfo=UTC)
        if seen_at.tzinfo is None:
            seen_at = seen_at.replace(tzinfo=UTC)

        return seen_at >= current_seen_at


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    normalized = (
        str(value)
        .strip()
        .replace("õ", "ő")
        .replace("Õ", "Ő")
        .replace("û", "ű")
        .replace("Û", "Ű")
    )
    return normalized or None


def _source_product_key(payload: Mapping[str, Any], product_name: str) -> str:
    source_product_id = _clean_text(
        payload.get("source_product_id") or payload.get("pos_product_id")
    )
    if source_product_id is not None:
        return f"id:{source_product_id.casefold()}"

    source_sku = _clean_text(payload.get("sku"))
    if source_sku is not None:
        return f"sku:{source_sku.casefold()}"

    source_barcode = _clean_text(payload.get("barcode"))
    if source_barcode is not None:
        return f"barcode:{source_barcode.casefold()}"

    return f"name:{product_name.casefold()}"


def _mapping_confidence(
    *,
    payload: Mapping[str, Any],
    product: ProductModel,
) -> str:
    source_sku = _clean_text(payload.get("sku"))
    if source_sku is not None and product.sku == source_sku:
        return "sku_auto"

    source_barcode = _clean_text(payload.get("barcode"))
    if source_barcode is not None:
        return "barcode_unverified"

    return "name_auto"


def _extract_seen_at(payload: Mapping[str, Any]) -> datetime | None:
    occurred_at = payload.get("occurred_at")
    if isinstance(occurred_at, str) and occurred_at:
        try:
            parsed = datetime.fromisoformat(occurred_at)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed

    value = payload.get("date")
    if isinstance(value, str) and value:
        try:
            return datetime.combine(date.fromisoformat(value), time.min, tzinfo=UTC)
        except ValueError:
            return None

    return None


def _earlier_datetime(current: datetime | None, candidate: datetime | None) -> datetime | None:
    if current is None:
        return candidate
    if candidate is None:
        return current
    return candidate if _comparable_datetime(candidate) < _comparable_datetime(current) else current


def _later_datetime(current: datetime | None, candidate: datetime | None) -> datetime | None:
    if current is None:
        return candidate
    if candidate is None:
        return current
    return candidate if _comparable_datetime(candidate) > _comparable_datetime(current) else current


def _comparable_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def _infer_product_type(category_name: str | None, *, fallback: str = "finished_good") -> str:
    if category_name is None:
        return fallback

    normalized = category_name.casefold()
    if any(token in normalized for token in ("jegy", "ticket", "belépő", "belepo")):
        return "service"
    if any(token in normalized for token in ("csomagolás", "csomagolas", "doboz")):
        return "packaging"
    return fallback or "finished_good"
