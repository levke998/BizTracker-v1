"""Procurement SQLAlchemy purchase invoice repository."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.modules.inventory.infrastructure.orm.inventory_item_model import (
    InventoryItemModel,
)
from app.modules.master_data.infrastructure.orm.business_unit_model import (
    BusinessUnitModel,
)
from app.modules.master_data.infrastructure.orm.unit_of_measure_model import (
    UnitOfMeasureModel,
)
from app.modules.procurement.domain.entities.purchase_invoice import (
    NewPurchaseInvoice,
    PurchaseInvoice,
    PurchaseInvoiceLine,
)
from app.modules.procurement.infrastructure.orm.purchase_invoice_line_model import (
    PurchaseInvoiceLineModel,
)
from app.modules.procurement.infrastructure.orm.purchase_invoice_model import (
    PurchaseInvoiceModel,
)
from app.modules.procurement.infrastructure.orm.supplier_model import SupplierModel


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
        return [
            self._to_entity(model=row[0], supplier_name=row[1])
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

    @staticmethod
    def _to_entity(
        *,
        model: PurchaseInvoiceModel,
        supplier_name: str,
    ) -> PurchaseInvoice:
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
                )
                for line in sorted(model.lines, key=lambda item: str(item.id))
            ),
        )
