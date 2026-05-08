"""Procurement SQLAlchemy purchase invoice repository."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, time
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.modules.finance.infrastructure.orm.transaction_model import (
    FinancialTransactionModel,
)
from app.modules.inventory.infrastructure.orm.inventory_item_model import (
    InventoryItemModel,
)
from app.modules.inventory.infrastructure.orm.inventory_movement_model import (
    InventoryMovementModel,
)
from app.modules.master_data.infrastructure.orm.business_unit_model import (
    BusinessUnitModel,
)
from app.modules.master_data.infrastructure.orm.unit_of_measure_model import (
    UnitOfMeasureModel,
)
from app.modules.master_data.infrastructure.orm.vat_rate_model import VatRateModel
from app.modules.procurement.domain.entities.purchase_invoice import (
    NewPurchaseInvoice,
    PurchaseInvoice,
    PurchaseInvoiceLine,
)
from app.modules.procurement.domain.repositories.purchase_invoice_repository import (
    PurchaseInvoicePostingResult,
)
from app.modules.procurement.infrastructure.orm.purchase_invoice_line_model import (
    PurchaseInvoiceLineModel,
)
from app.modules.procurement.infrastructure.orm.purchase_invoice_model import (
    PurchaseInvoiceModel,
)
from app.modules.procurement.infrastructure.orm.supplier_model import SupplierModel

FINANCE_SOURCE_TYPE = "supplier_invoice"
INVENTORY_SOURCE_TYPE = "supplier_invoice_line"
FINANCE_TRANSACTION_TYPE = "supplier_invoice"
FINANCE_DIRECTION = "outflow"
INVENTORY_MOVEMENT_TYPE = "purchase"
UNIT_COST_QUANT = Decimal("0.01")
PostingMetadata = dict[uuid.UUID, tuple[bool, int]]


class SqlAlchemyPurchaseInvoiceRepository:
    """SQLAlchemy repository for procurement purchase invoices."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def list_many(
        self,
        *,
        business_unit_id: uuid.UUID | None = None,
        supplier_id: uuid.UUID | None = None,
        limit: int = 50,
    ) -> list[PurchaseInvoice]:
        statement = (
            select(PurchaseInvoiceModel, SupplierModel.name)
            .join(SupplierModel, SupplierModel.id == PurchaseInvoiceModel.supplier_id)
            .options(selectinload(PurchaseInvoiceModel.lines))
        )

        if business_unit_id is not None:
            statement = statement.where(
                PurchaseInvoiceModel.business_unit_id == business_unit_id
            )
        if supplier_id is not None:
            statement = statement.where(PurchaseInvoiceModel.supplier_id == supplier_id)

        statement = statement.order_by(
            PurchaseInvoiceModel.invoice_date.desc(),
            PurchaseInvoiceModel.created_at.desc(),
        ).limit(limit)

        rows = self._session.execute(statement).all()
        posting_metadata = self._get_posting_metadata(
            [row[0].id for row in rows],
        )
        return [
            self._to_entity(
                model=row[0],
                supplier_name=row[1],
                posting_metadata=posting_metadata.get(row[0].id),
            )
            for row in rows
        ]

    def create(self, invoice: NewPurchaseInvoice) -> PurchaseInvoice:
        model = PurchaseInvoiceModel(
            business_unit_id=invoice.business_unit_id,
            supplier_id=invoice.supplier_id,
            invoice_number=invoice.invoice_number,
            invoice_date=invoice.invoice_date,
            currency=invoice.currency,
            gross_total=invoice.gross_total,
            notes=invoice.notes,
            lines=[
                PurchaseInvoiceLineModel(
                    inventory_item_id=line.inventory_item_id,
                    description=line.description,
                    quantity=line.quantity,
                    uom_id=line.uom_id,
                    unit_net_amount=line.unit_net_amount,
                    line_net_amount=line.line_net_amount,
                    vat_rate_id=line.vat_rate_id,
                    vat_amount=line.vat_amount,
                    line_gross_amount=line.line_gross_amount,
                )
                for line in invoice.lines
            ],
        )
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        supplier_name = self._session.scalar(
            select(SupplierModel.name).where(SupplierModel.id == model.supplier_id)
        )
        return self._to_entity(model=model, supplier_name=supplier_name or "")

    def get_by_id(self, purchase_invoice_id: uuid.UUID) -> PurchaseInvoice | None:
        statement = (
            select(PurchaseInvoiceModel, SupplierModel.name)
            .join(SupplierModel, SupplierModel.id == PurchaseInvoiceModel.supplier_id)
            .options(selectinload(PurchaseInvoiceModel.lines))
            .where(PurchaseInvoiceModel.id == purchase_invoice_id)
        )
        row = self._session.execute(statement).one_or_none()
        if row is None:
            return None
        posting_metadata = self._get_posting_metadata([row[0].id])
        return self._to_entity(
            model=row[0],
            supplier_name=row[1],
            posting_metadata=posting_metadata.get(row[0].id),
        )

    def has_posting_for_invoice(self, purchase_invoice_id: uuid.UUID) -> bool:
        finance_count = self._session.scalar(
            select(func.count())
            .select_from(FinancialTransactionModel)
            .where(FinancialTransactionModel.source_type == FINANCE_SOURCE_TYPE)
            .where(FinancialTransactionModel.source_id == purchase_invoice_id)
        )
        if finance_count:
            return True

        line_ids = [
            line_id
            for line_id, in self._session.execute(
                select(PurchaseInvoiceLineModel.id).where(
                    PurchaseInvoiceLineModel.invoice_id == purchase_invoice_id
                )
            ).all()
        ]
        if not line_ids:
            return False

        movement_count = self._session.scalar(
            select(func.count())
            .select_from(InventoryMovementModel)
            .where(InventoryMovementModel.source_type == INVENTORY_SOURCE_TYPE)
            .where(InventoryMovementModel.source_id.in_(line_ids))
        )
        return bool(movement_count)

    def post_to_actuals(self, invoice: PurchaseInvoice) -> PurchaseInvoicePostingResult:
        occurred_at = datetime.combine(invoice.invoice_date, time.min, tzinfo=UTC)
        updated_inventory_item_costs = self._update_inventory_item_default_costs(
            invoice=invoice,
            occurred_at=occurred_at,
        )
        finance_transaction = FinancialTransactionModel(
            business_unit_id=invoice.business_unit_id,
            direction=FINANCE_DIRECTION,
            transaction_type=FINANCE_TRANSACTION_TYPE,
            amount=invoice.gross_total,
            currency=invoice.currency,
            occurred_at=occurred_at,
            description=(
                f"Supplier invoice {invoice.invoice_number} - {invoice.supplier_name}"
            ),
            source_type=FINANCE_SOURCE_TYPE,
            source_id=invoice.id,
        )

        inventory_movements = [
            InventoryMovementModel(
                business_unit_id=invoice.business_unit_id,
                inventory_item_id=line.inventory_item_id,
                movement_type=INVENTORY_MOVEMENT_TYPE,
                quantity=line.quantity,
                uom_id=line.uom_id,
                unit_cost=(line.line_net_amount / line.quantity).quantize(UNIT_COST_QUANT),
                note=f"Supplier invoice {invoice.invoice_number}: {line.description}",
                source_type=INVENTORY_SOURCE_TYPE,
                source_id=line.id,
                occurred_at=occurred_at,
            )
            for line in invoice.lines
            if line.inventory_item_id is not None
        ]

        try:
            self._session.add(finance_transaction)
            self._session.add_all(inventory_movements)
            self._session.commit()
        except Exception:
            self._session.rollback()
            raise

        return PurchaseInvoicePostingResult(
            purchase_invoice_id=invoice.id,
            created_financial_transactions=1,
            created_inventory_movements=len(inventory_movements),
            updated_inventory_item_costs=updated_inventory_item_costs,
            finance_source_type=FINANCE_SOURCE_TYPE,
            inventory_source_type=INVENTORY_SOURCE_TYPE,
        )

    def _update_inventory_item_default_costs(
        self,
        *,
        invoice: PurchaseInvoice,
        occurred_at: datetime,
    ) -> int:
        updated_count = 0
        for line in invoice.lines:
            if line.inventory_item_id is None:
                continue

            item = self._session.get(InventoryItemModel, line.inventory_item_id)
            if item is None:
                continue
            if item.default_unit_cost_last_seen_at is not None and (
                item.default_unit_cost_last_seen_at > occurred_at
            ):
                continue

            unit_cost = (line.line_net_amount / line.quantity).quantize(UNIT_COST_QUANT)
            if (
                item.default_unit_cost == unit_cost
                and item.default_unit_cost_source_id == line.id
                and item.default_unit_cost_source_type == INVENTORY_SOURCE_TYPE
            ):
                continue

            item.default_unit_cost = unit_cost
            item.default_unit_cost_last_seen_at = occurred_at
            item.default_unit_cost_source_type = INVENTORY_SOURCE_TYPE
            item.default_unit_cost_source_id = line.id
            updated_count += 1

        return updated_count

    def _get_posting_metadata(
        self,
        purchase_invoice_ids: list[uuid.UUID],
    ) -> PostingMetadata:
        if not purchase_invoice_ids:
            return {}

        finance_source_ids = set(
            self._session.scalars(
                select(FinancialTransactionModel.source_id)
                .where(FinancialTransactionModel.source_type == FINANCE_SOURCE_TYPE)
                .where(FinancialTransactionModel.source_id.in_(purchase_invoice_ids))
            ).all()
        )

        movement_rows = self._session.execute(
            select(
                PurchaseInvoiceLineModel.invoice_id,
                func.count(InventoryMovementModel.id),
            )
            .select_from(PurchaseInvoiceLineModel)
            .join(
                InventoryMovementModel,
                InventoryMovementModel.source_id == PurchaseInvoiceLineModel.id,
            )
            .where(InventoryMovementModel.source_type == INVENTORY_SOURCE_TYPE)
            .where(PurchaseInvoiceLineModel.invoice_id.in_(purchase_invoice_ids))
            .group_by(PurchaseInvoiceLineModel.invoice_id)
        ).all()
        movement_counts = {
            invoice_id: int(count)
            for invoice_id, count in movement_rows
        }

        return {
            invoice_id: (
                invoice_id in finance_source_ids,
                movement_counts.get(invoice_id, 0),
            )
            for invoice_id in purchase_invoice_ids
        }

    def business_unit_exists(self, business_unit_id: uuid.UUID) -> bool:
        count = self._session.scalar(
            select(func.count())
            .select_from(BusinessUnitModel)
            .where(BusinessUnitModel.id == business_unit_id)
        )
        return bool(count)

    def supplier_exists(self, supplier_id: uuid.UUID) -> bool:
        count = self._session.scalar(
            select(func.count())
            .select_from(SupplierModel)
            .where(SupplierModel.id == supplier_id)
        )
        return bool(count)

    def supplier_belongs_to_business_unit(
        self,
        *,
        supplier_id: uuid.UUID,
        business_unit_id: uuid.UUID,
    ) -> bool:
        count = self._session.scalar(
            select(func.count())
            .select_from(SupplierModel)
            .where(SupplierModel.id == supplier_id)
            .where(SupplierModel.business_unit_id == business_unit_id)
        )
        return bool(count)

    def invoice_number_exists(
        self,
        *,
        business_unit_id: uuid.UUID,
        supplier_id: uuid.UUID,
        invoice_number: str,
    ) -> bool:
        count = self._session.scalar(
            select(func.count())
            .select_from(PurchaseInvoiceModel)
            .where(PurchaseInvoiceModel.business_unit_id == business_unit_id)
            .where(PurchaseInvoiceModel.supplier_id == supplier_id)
            .where(PurchaseInvoiceModel.invoice_number == invoice_number)
        )
        return bool(count)

    def unit_of_measure_exists(self, uom_id: uuid.UUID) -> bool:
        count = self._session.scalar(
            select(func.count())
            .select_from(UnitOfMeasureModel)
            .where(UnitOfMeasureModel.id == uom_id)
        )
        return bool(count)

    def inventory_item_exists(self, inventory_item_id: uuid.UUID) -> bool:
        count = self._session.scalar(
            select(func.count())
            .select_from(InventoryItemModel)
            .where(InventoryItemModel.id == inventory_item_id)
        )
        return bool(count)

    def inventory_item_belongs_to_business_unit(
        self,
        *,
        inventory_item_id: uuid.UUID,
        business_unit_id: uuid.UUID,
    ) -> bool:
        count = self._session.scalar(
            select(func.count())
            .select_from(InventoryItemModel)
            .where(InventoryItemModel.id == inventory_item_id)
            .where(InventoryItemModel.business_unit_id == business_unit_id)
        )
        return bool(count)

    def inventory_item_matches_uom(
        self,
        *,
        inventory_item_id: uuid.UUID,
        uom_id: uuid.UUID,
    ) -> bool:
        count = self._session.scalar(
            select(func.count())
            .select_from(InventoryItemModel)
            .where(InventoryItemModel.id == inventory_item_id)
            .where(InventoryItemModel.uom_id == uom_id)
        )
        return bool(count)

    def vat_rate_exists(self, vat_rate_id: uuid.UUID) -> bool:
        count = self._session.scalar(
            select(func.count()).select_from(VatRateModel).where(VatRateModel.id == vat_rate_id)
        )
        return bool(count)

    @staticmethod
    def _to_entity(
        *,
        model: PurchaseInvoiceModel,
        supplier_name: str,
        posting_metadata: tuple[bool, int] | None = None,
    ) -> PurchaseInvoice:
        posted_to_finance, posted_inventory_movement_count = posting_metadata or (False, 0)
        return PurchaseInvoice(
            id=model.id,
            business_unit_id=model.business_unit_id,
            supplier_id=model.supplier_id,
            supplier_name=supplier_name,
            invoice_number=model.invoice_number,
            invoice_date=model.invoice_date,
            currency=model.currency,
            gross_total=model.gross_total,
            notes=model.notes,
            is_posted=posted_to_finance or posted_inventory_movement_count > 0,
            posted_to_finance=posted_to_finance,
            posted_inventory_movement_count=posted_inventory_movement_count,
            created_at=model.created_at,
            updated_at=model.updated_at,
            lines=tuple(
                PurchaseInvoiceLine(
                    id=line.id,
                    inventory_item_id=line.inventory_item_id,
                    description=line.description,
                    quantity=line.quantity,
                    uom_id=line.uom_id,
                    unit_net_amount=line.unit_net_amount,
                    line_net_amount=line.line_net_amount,
                    vat_rate_id=line.vat_rate_id,
                    vat_amount=line.vat_amount,
                    line_gross_amount=line.line_gross_amount,
                )
                for line in sorted(model.lines, key=lambda item: str(item.id))
            ),
        )
