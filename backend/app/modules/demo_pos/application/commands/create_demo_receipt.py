"""Create demo POS receipts through the import and finance pipeline."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.finance.infrastructure.orm.transaction_model import (
    FinancialTransactionModel,
)
from app.modules.imports.infrastructure.orm.import_batch_model import ImportBatchModel
from app.modules.imports.infrastructure.orm.import_file_model import ImportFileModel
from app.modules.imports.infrastructure.orm.import_row_model import ImportRowModel
from app.modules.inventory.infrastructure.orm.inventory_item_model import (
    InventoryItemModel,
)
from app.modules.master_data.infrastructure.orm.business_unit_model import (
    BusinessUnitModel,
)
from app.modules.master_data.infrastructure.orm.category_model import CategoryModel
from app.modules.master_data.infrastructure.orm.product_model import ProductModel
from app.modules.master_data.infrastructure.orm.unit_of_measure_model import (
    UnitOfMeasureModel,
)
from app.modules.production.infrastructure.orm.recipe_model import (
    RecipeIngredientModel,
    RecipeModel,
    RecipeVersionModel,
)
from app.modules.pos_ingestion.application.services.pos_sale_identity import (
    build_pos_sale_dedupe_key,
)
from app.modules.pos_ingestion.application.services.pos_sale_inventory import (
    PosSaleInventoryConsumptionService,
)

APP_TIME_ZONE = ZoneInfo("Europe/Budapest")


class DemoPosBusinessUnitNotFoundError(Exception):
    """Raised when the selected business unit does not exist."""


class DemoPosProductNotFoundError(Exception):
    """Raised when a receipt line references an unavailable product."""


class DemoPosValidationError(Exception):
    """Raised when a receipt cannot be accepted."""


@dataclass(frozen=True, slots=True)
class NewDemoPosReceiptLine:
    """Input line for a demo POS receipt."""

    product_id: uuid.UUID
    quantity: Decimal


@dataclass(frozen=True, slots=True)
class CreatedDemoPosReceiptLine:
    """One persisted receipt line summary."""

    product_id: uuid.UUID
    product_name: str
    category_name: str | None
    quantity: Decimal
    unit_price_gross: Decimal
    gross_amount: Decimal
    import_row_id: uuid.UUID
    transaction_id: uuid.UUID


@dataclass(frozen=True, slots=True)
class CreatedDemoPosReceipt:
    """Created demo POS receipt summary."""

    business_unit_id: uuid.UUID
    receipt_no: str
    payment_method: str
    occurred_at: datetime
    batch_id: uuid.UUID
    gross_total: Decimal
    transaction_count: int
    lines: tuple[CreatedDemoPosReceiptLine, ...]


class CreateDemoPosReceiptCommand:
    """Create staging import rows and finance transactions from one receipt."""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._inventory_consumption = PosSaleInventoryConsumptionService(session)

    def execute(
        self,
        *,
        business_unit_id: uuid.UUID,
        payment_method: str,
        lines: list[NewDemoPosReceiptLine],
        receipt_no: str | None = None,
        occurred_at: datetime | None = None,
    ) -> CreatedDemoPosReceipt:
        if not lines:
            raise DemoPosValidationError("A receipt must contain at least one line.")

        business_unit = self._session.get(BusinessUnitModel, business_unit_id)
        if business_unit is None or not business_unit.is_active:
            raise DemoPosBusinessUnitNotFoundError(
                f"Business unit {business_unit_id} was not found."
            )

        occurred_at = occurred_at or datetime.now(UTC)
        if occurred_at.tzinfo is None:
            occurred_at = occurred_at.replace(tzinfo=UTC)
        business_date = occurred_at.astimezone(APP_TIME_ZONE).date()

        receipt_no = receipt_no or self._build_receipt_number(business_unit.code)
        normalized_payment_method = payment_method.strip().lower() or "card"
        product_ids = [line.product_id for line in lines]
        products = self._load_products(business_unit_id, product_ids)

        missing_ids = set(product_ids) - set(products)
        if missing_ids:
            raise DemoPosProductNotFoundError(
                "One or more products are not available for this business unit."
            )

        try:
            batch = ImportBatchModel(
                business_unit_id=business_unit_id,
                import_type="pos_sales",
                status="parsed",
                started_at=occurred_at,
                finished_at=occurred_at,
                total_rows=len(lines),
                parsed_rows=len(lines),
                error_rows=0,
            )
            self._session.add(batch)
            self._session.flush()

            import_file = ImportFileModel(
                batch_id=batch.id,
                original_name=f"{receipt_no}.demo-pos-api.json",
                stored_path=f"demo-pos-api://{receipt_no}",
                mime_type="application/json",
                size_bytes=0,
            )
            self._session.add(import_file)
            self._session.flush()

            created_lines: list[CreatedDemoPosReceiptLine] = []
            transactions: list[FinancialTransactionModel] = []
            gross_total = Decimal("0")

            for row_number, line in enumerate(lines, start=2):
                product = products[line.product_id]
                if product.sale_price_gross is None:
                    raise DemoPosValidationError(
                        f"Product {product.name!r} does not have a sale price."
                    )
                if line.quantity <= 0:
                    raise DemoPosValidationError("Receipt line quantity must be positive.")

                unit_price = Decimal(product.sale_price_gross)
                gross_amount = (unit_price * line.quantity).quantize(Decimal("0.01"))
                category_name = product.category.name if product.category else None
                payload = {
                    "date": business_date.isoformat(),
                    "occurred_at": occurred_at.isoformat(),
                    "receipt_no": receipt_no,
                    "product_id": str(product.id),
                    "sku": product.sku,
                    "category_name": category_name,
                    "product_name": product.name,
                    "quantity": _json_number(line.quantity),
                    "unit_price_gross": _json_number(unit_price),
                    "gross_amount": _json_number(gross_amount),
                    "payment_method": normalized_payment_method,
                }
                dedupe_key = build_pos_sale_dedupe_key(
                    business_unit_id=business_unit_id,
                    payload=payload,
                )
                payload["dedupe_key"] = dedupe_key
                if self._dedupe_key_exists(dedupe_key):
                    continue

                self._inventory_consumption.consume_line(
                    business_unit_id=business_unit_id,
                    payload=payload,
                )
                gross_total += gross_amount
                import_row = ImportRowModel(
                    batch_id=batch.id,
                    file_id=import_file.id,
                    row_number=row_number,
                    raw_payload=payload,
                    normalized_payload=payload,
                    parse_status="parsed",
                )
                self._session.add(import_row)
                self._session.flush()

                transaction = FinancialTransactionModel(
                    business_unit_id=business_unit_id,
                    direction="inflow",
                    transaction_type="pos_sale",
                    amount=gross_amount,
                    currency=product.currency,
                    occurred_at=occurred_at,
                    description=f"{product.name} ({receipt_no})",
                    source_type="import_row",
                    source_id=import_row.id,
                    dedupe_key=dedupe_key,
                )
                self._session.add(transaction)
                transactions.append(transaction)
                self._session.flush()

                created_lines.append(
                    CreatedDemoPosReceiptLine(
                        product_id=product.id,
                        product_name=product.name,
                        category_name=category_name,
                        quantity=line.quantity,
                        unit_price_gross=unit_price,
                        gross_amount=gross_amount,
                        import_row_id=import_row.id,
                        transaction_id=transaction.id,
                    )
                )

            batch.parsed_rows = len(created_lines)
            self._session.commit()
        except Exception:
            self._session.rollback()
            raise

        return CreatedDemoPosReceipt(
            business_unit_id=business_unit_id,
            receipt_no=receipt_no,
            payment_method=normalized_payment_method,
            occurred_at=occurred_at,
            batch_id=batch.id,
            gross_total=gross_total.quantize(Decimal("0.01")),
            transaction_count=len(transactions),
            lines=tuple(created_lines),
        )

    def _load_products(
        self,
        business_unit_id: uuid.UUID,
        product_ids: list[uuid.UUID],
    ) -> dict[uuid.UUID, ProductModel]:
        rows = self._session.scalars(
            select(ProductModel)
            .where(ProductModel.business_unit_id == business_unit_id)
            .where(ProductModel.id.in_(product_ids))
            .where(ProductModel.is_active.is_(True))
        ).all()
        return {product.id: product for product in rows}

    def _dedupe_key_exists(self, dedupe_key: str) -> bool:
        return (
            self._session.scalar(
                select(FinancialTransactionModel.id)
                .where(FinancialTransactionModel.dedupe_key == dedupe_key)
                .limit(1)
            )
            is not None
        )

    def _apply_estimated_stock_consumption(
        self,
        *,
        product: ProductModel,
        sold_quantity: Decimal,
    ) -> None:
        recipe_version = self._session.scalar(
            select(RecipeVersionModel)
            .join(RecipeModel, RecipeModel.id == RecipeVersionModel.recipe_id)
            .where(RecipeModel.product_id == product.id)
            .where(RecipeModel.is_active.is_(True))
            .where(RecipeVersionModel.is_active.is_(True))
            .order_by(RecipeVersionModel.version_no.desc())
            .limit(1)
        )
        if recipe_version is not None:
            self._consume_recipe_stock(
                recipe_version=recipe_version,
                sold_quantity=sold_quantity,
            )
            return

        self._consume_direct_stock(product=product, sold_quantity=sold_quantity)

    def _consume_recipe_stock(
        self,
        *,
        recipe_version: RecipeVersionModel,
        sold_quantity: Decimal,
    ) -> None:
        yield_quantity = Decimal(recipe_version.yield_quantity)
        if yield_quantity <= 0:
            return

        ingredients = self._session.scalars(
            select(RecipeIngredientModel).where(
                RecipeIngredientModel.recipe_version_id == recipe_version.id
            )
        ).all()
        for ingredient in ingredients:
            item = self._session.get(InventoryItemModel, ingredient.inventory_item_id)
            if item is None or item.estimated_stock_quantity is None:
                continue

            quantity = Decimal(ingredient.quantity) * sold_quantity / yield_quantity
            converted_quantity = self._convert_quantity(
                quantity,
                from_uom=self._get_uom_code(ingredient.uom_id),
                to_uom=self._get_uom_code(item.uom_id),
            )
            if converted_quantity is None:
                continue
            self._decrease_estimated_stock(item, converted_quantity)

    def _consume_direct_stock(
        self,
        *,
        product: ProductModel,
        sold_quantity: Decimal,
    ) -> None:
        item = self._session.scalar(
            select(InventoryItemModel)
            .where(InventoryItemModel.business_unit_id == product.business_unit_id)
            .where(InventoryItemModel.name == product.name)
            .where(InventoryItemModel.track_stock.is_(True))
            .where(InventoryItemModel.is_active.is_(True))
            .limit(1)
        )
        if item is None or item.estimated_stock_quantity is None:
            return

        converted_quantity = self._convert_quantity(
            sold_quantity,
            from_uom=self._get_uom_code(product.sales_uom_id),
            to_uom=self._get_uom_code(item.uom_id),
        )
        if converted_quantity is None:
            return
        self._decrease_estimated_stock(item, converted_quantity)

    @staticmethod
    def _decrease_estimated_stock(
        item: InventoryItemModel,
        quantity: Decimal,
    ) -> None:
        current_quantity = Decimal(item.estimated_stock_quantity or 0)
        item.estimated_stock_quantity = max(
            Decimal("0"),
            current_quantity - quantity,
        ).quantize(Decimal("0.001"))

    def _get_uom_code(self, uom_id: uuid.UUID | None) -> str | None:
        if uom_id is None:
            return None
        unit = self._session.get(UnitOfMeasureModel, uom_id)
        return unit.code if unit else None

    @staticmethod
    def _convert_quantity(
        quantity: Decimal,
        *,
        from_uom: str | None,
        to_uom: str | None,
    ) -> Decimal | None:
        if from_uom == to_uom:
            return quantity
        if from_uom is None or to_uom is None:
            return None

        factors = {
            "g": ("mass", Decimal("0.001")),
            "kg": ("mass", Decimal("1")),
            "ml": ("volume", Decimal("0.001")),
            "l": ("volume", Decimal("1")),
        }
        from_factor = factors.get(from_uom)
        to_factor = factors.get(to_uom)
        if from_factor is None or to_factor is None or from_factor[0] != to_factor[0]:
            return None

        return (quantity * from_factor[1]) / to_factor[1]

    @staticmethod
    def _build_receipt_number(business_unit_code: str) -> str:
        timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        suffix = uuid.uuid4().hex[:6].upper()
        return f"DEMO-{business_unit_code.upper()}-{timestamp}-{suffix}"


def _json_number(value: Decimal) -> int | float:
    if value == value.to_integral_value():
        return int(value)
    return float(value)
