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
from app.modules.master_data.infrastructure.orm.business_unit_model import (
    BusinessUnitModel,
)
from app.modules.master_data.infrastructure.orm.category_model import CategoryModel
from app.modules.master_data.infrastructure.orm.product_model import ProductModel

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
                gross_total += gross_amount
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

    @staticmethod
    def _build_receipt_number(business_unit_code: str) -> str:
        timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        suffix = uuid.uuid4().hex[:6].upper()
        return f"DEMO-{business_unit_code.upper()}-{timestamp}-{suffix}"


def _json_number(value: Decimal) -> int | float:
    if value == value.to_integral_value():
        return int(value)
    return float(value)
