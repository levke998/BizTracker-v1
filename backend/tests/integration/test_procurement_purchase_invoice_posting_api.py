"""Integration tests for purchase invoice downstream posting."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.finance.infrastructure.orm.transaction_model import (
    FinancialTransactionModel,
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

API_PREFIX = "/api/v1/procurement"


def test_post_purchase_invoice_creates_finance_and_inventory_actuals(
    client: TestClient,
    db_session: Session,
    test_business_unit: BusinessUnitModel,
    test_unit_of_measure: UnitOfMeasureModel,
    create_supplier,
    create_inventory_item,
    create_purchase_invoice,
) -> None:
    supplier = create_supplier(
        business_unit_id=test_business_unit.id,
        name="Posting Supplier",
    )
    flour = create_inventory_item(
        business_unit_id=test_business_unit.id,
        uom_id=test_unit_of_measure.id,
        name="Posting Flour",
        item_type="raw_material",
    )
    invoice = create_purchase_invoice(
        business_unit_id=test_business_unit.id,
        supplier_id=supplier.id,
        invoice_number="POST-2026-001",
        invoice_date=date(2026, 4, 24),
        currency="HUF",
        gross_total=Decimal("12700.00"),
        lines=[
            {
                "inventory_item_id": flour.id,
                "description": "Flour 25 kg",
                "quantity": Decimal("25.000"),
                "uom_id": test_unit_of_measure.id,
                "unit_net_amount": Decimal("400.00"),
                "line_net_amount": Decimal("10000.00"),
            },
            {
                "description": "Delivery fee",
                "quantity": Decimal("1.000"),
                "uom_id": test_unit_of_measure.id,
                "unit_net_amount": Decimal("700.00"),
                "line_net_amount": Decimal("700.00"),
            },
        ],
    )

    response = client.post(f"{API_PREFIX}/purchase-invoices/{invoice.id}/post")

    assert response.status_code == 200
    payload = response.json()
    assert payload["purchase_invoice_id"] == str(invoice.id)
    assert payload["created_financial_transactions"] == 1
    assert payload["created_inventory_movements"] == 1
    assert payload["finance_source_type"] == "supplier_invoice"
    assert payload["inventory_source_type"] == "supplier_invoice_line"

    db_session.expire_all()
    transaction = db_session.scalar(
        select(FinancialTransactionModel).where(
            FinancialTransactionModel.source_id == invoice.id,
            FinancialTransactionModel.source_type == "supplier_invoice",
        )
    )
    assert transaction is not None
    assert transaction.direction == "outflow"
    assert transaction.transaction_type == "supplier_invoice"
    assert transaction.amount == Decimal("12700.00")

    movement = db_session.scalar(
        select(InventoryMovementModel).where(
            InventoryMovementModel.business_unit_id == test_business_unit.id,
            InventoryMovementModel.source_type == "supplier_invoice_line",
        )
    )
    assert movement is not None
    assert movement.inventory_item_id == flour.id
    assert movement.movement_type == "purchase"
    assert movement.quantity == Decimal("25.000")
    assert movement.unit_cost == Decimal("400.00")

    list_response = client.get(
        f"{API_PREFIX}/purchase-invoices",
        params={"business_unit_id": str(test_business_unit.id)},
    )
    assert list_response.status_code == 200
    posted_invoice = next(
        item
        for item in list_response.json()
        if item["id"] == str(invoice.id)
    )
    assert posted_invoice["is_posted"] is True
    assert posted_invoice["posted_to_finance"] is True
    assert posted_invoice["posted_inventory_movement_count"] == 1


def test_post_purchase_invoice_is_idempotency_guarded(
    client: TestClient,
    test_business_unit: BusinessUnitModel,
    test_unit_of_measure: UnitOfMeasureModel,
    create_supplier,
    create_inventory_item,
    create_purchase_invoice,
) -> None:
    supplier = create_supplier(
        business_unit_id=test_business_unit.id,
        name="Duplicate Posting Supplier",
    )
    item = create_inventory_item(
        business_unit_id=test_business_unit.id,
        uom_id=test_unit_of_measure.id,
        name="Duplicate Posting Item",
        item_type="raw_material",
    )
    invoice = create_purchase_invoice(
        business_unit_id=test_business_unit.id,
        supplier_id=supplier.id,
        invoice_number="POST-2026-DUP",
        invoice_date=date(2026, 4, 24),
        currency="HUF",
        gross_total=Decimal("1000.00"),
        lines=[
            {
                "inventory_item_id": item.id,
                "description": "Tracked item",
                "quantity": Decimal("2.000"),
                "uom_id": test_unit_of_measure.id,
                "unit_net_amount": Decimal("500.00"),
                "line_net_amount": Decimal("1000.00"),
            }
        ],
    )

    first_response = client.post(f"{API_PREFIX}/purchase-invoices/{invoice.id}/post")
    assert first_response.status_code == 200

    second_response = client.post(f"{API_PREFIX}/purchase-invoices/{invoice.id}/post")

    assert second_response.status_code == 409
    assert "already been posted" in second_response.json()["detail"]


def test_post_unknown_purchase_invoice_returns_not_found(client: TestClient) -> None:
    response = client.post(f"{API_PREFIX}/purchase-invoices/{uuid4()}/post")

    assert response.status_code == 404
    assert "Purchase invoice" in response.json()["detail"]
