"""Integration tests for procurement purchase invoice APIs."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient

from app.modules.master_data.infrastructure.orm.business_unit_model import (
    BusinessUnitModel,
)
from app.modules.master_data.infrastructure.orm.unit_of_measure_model import (
    UnitOfMeasureModel,
)
from app.modules.procurement.infrastructure.orm.supplier_model import SupplierModel

API_PREFIX = "/api/v1/procurement"


def test_create_purchase_invoice_succeeds(
    client: TestClient,
    test_business_unit: BusinessUnitModel,
    test_unit_of_measure: UnitOfMeasureModel,
    create_supplier,
    create_inventory_item,
) -> None:
    supplier = create_supplier(
        business_unit_id=test_business_unit.id,
        name="Molnar Alapanyag Kft",
    )
    inventory_item = create_inventory_item(
        business_unit_id=test_business_unit.id,
        uom_id=test_unit_of_measure.id,
        name="Fine Flour",
        item_type="raw_material",
    )

    response = client.post(
        f"{API_PREFIX}/purchase-invoices",
        json={
            "business_unit_id": str(test_business_unit.id),
            "supplier_id": str(supplier.id),
            "invoice_number": "INV-2026-001",
            "invoice_date": "2026-04-23",
            "currency": "HUF",
            "gross_total": "12500.00",
            "notes": "Manual bakery purchase",
            "lines": [
                {
                    "inventory_item_id": str(inventory_item.id),
                    "description": "Fine Flour 25 kg",
                    "quantity": "25.000",
                    "uom_id": str(test_unit_of_measure.id),
                    "unit_net_amount": "400.00",
                    "line_net_amount": "10000.00",
                }
            ],
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["business_unit_id"] == str(test_business_unit.id)
    assert payload["supplier_id"] == str(supplier.id)
    assert payload["supplier_name"] == "Molnar Alapanyag Kft"
    assert payload["invoice_number"] == "INV-2026-001"
    assert payload["gross_total"] == "12500.00"
    assert payload["is_posted"] is False
    assert payload["posted_to_finance"] is False
    assert payload["posted_inventory_movement_count"] == 0
    assert len(payload["lines"]) == 1
    assert payload["lines"][0]["inventory_item_id"] == str(inventory_item.id)


def test_create_purchase_invoice_with_invalid_supplier_returns_not_found(
    client: TestClient,
    test_business_unit: BusinessUnitModel,
    test_unit_of_measure: UnitOfMeasureModel,
) -> None:
    response = client.post(
        f"{API_PREFIX}/purchase-invoices",
        json={
            "business_unit_id": str(test_business_unit.id),
            "supplier_id": str(uuid4()),
            "invoice_number": "INV-2026-404",
            "invoice_date": "2026-04-23",
            "currency": "HUF",
            "gross_total": "1000.00",
            "lines": [
                {
                    "description": "Test line",
                    "quantity": "1.000",
                    "uom_id": str(test_unit_of_measure.id),
                    "unit_net_amount": "1000.00",
                    "line_net_amount": "1000.00",
                }
            ],
        },
    )

    assert response.status_code == 404
    assert "Supplier" in response.json()["detail"]


def test_create_purchase_invoice_rejects_supplier_from_other_business_unit(
    client: TestClient,
    test_business_unit: BusinessUnitModel,
    gourmand_business_unit: BusinessUnitModel,
    test_unit_of_measure: UnitOfMeasureModel,
    create_supplier,
) -> None:
    supplier = create_supplier(
        business_unit_id=gourmand_business_unit.id,
        name=f"Other Unit Supplier {uuid4().hex[:8]}",
    )

    response = client.post(
        f"{API_PREFIX}/purchase-invoices",
        json={
            "business_unit_id": str(test_business_unit.id),
            "supplier_id": str(supplier.id),
            "invoice_number": "INV-2026-422",
            "invoice_date": "2026-04-23",
            "currency": "HUF",
            "gross_total": "1000.00",
            "lines": [
                {
                    "description": "Mismatch line",
                    "quantity": "1.000",
                    "uom_id": str(test_unit_of_measure.id),
                    "unit_net_amount": "1000.00",
                    "line_net_amount": "1000.00",
                }
            ],
        },
    )

    assert response.status_code == 422
    assert "does not belong" in response.json()["detail"]


def test_create_purchase_invoice_with_invalid_uom_returns_not_found(
    client: TestClient,
    test_business_unit: BusinessUnitModel,
    create_supplier,
) -> None:
    supplier = create_supplier(
        business_unit_id=test_business_unit.id,
        name="Uom Test Supplier",
    )

    response = client.post(
        f"{API_PREFIX}/purchase-invoices",
        json={
            "business_unit_id": str(test_business_unit.id),
            "supplier_id": str(supplier.id),
            "invoice_number": "INV-2026-UOM",
            "invoice_date": "2026-04-23",
            "currency": "HUF",
            "gross_total": "1000.00",
            "lines": [
                {
                    "description": "Unknown UOM line",
                    "quantity": "1.000",
                    "uom_id": str(uuid4()),
                    "unit_net_amount": "1000.00",
                    "line_net_amount": "1000.00",
                }
            ],
        },
    )

    assert response.status_code == 404
    assert "Unit of measure" in response.json()["detail"]


def test_create_purchase_invoice_rejects_duplicate_invoice_number_for_same_supplier(
    client: TestClient,
    test_business_unit: BusinessUnitModel,
    test_unit_of_measure: UnitOfMeasureModel,
    create_supplier,
) -> None:
    supplier = create_supplier(
        business_unit_id=test_business_unit.id,
        name="Duplicate Invoice Supplier",
    )
    payload = {
        "business_unit_id": str(test_business_unit.id),
        "supplier_id": str(supplier.id),
        "invoice_number": "INV-2026-DUP",
        "invoice_date": "2026-04-23",
        "currency": "HUF",
        "gross_total": "1000.00",
        "lines": [
            {
                "description": "Duplicate line",
                "quantity": "1.000",
                "uom_id": str(test_unit_of_measure.id),
                "unit_net_amount": "1000.00",
                "line_net_amount": "1000.00",
            }
        ],
    }

    first_response = client.post(f"{API_PREFIX}/purchase-invoices", json=payload)
    assert first_response.status_code == 201

    second_response = client.post(f"{API_PREFIX}/purchase-invoices", json=payload)
    assert second_response.status_code == 409
    assert "already exists" in second_response.json()["detail"]


def test_list_purchase_invoices_filters_and_orders_results(
    client: TestClient,
    test_business_unit: BusinessUnitModel,
    test_unit_of_measure: UnitOfMeasureModel,
    create_supplier,
    create_purchase_invoice,
) -> None:
    alpha_supplier = create_supplier(
        business_unit_id=test_business_unit.id,
        name="Alpha Trade",
    )
    beta_supplier = create_supplier(
        business_unit_id=test_business_unit.id,
        name="Beta Trade",
    )

    create_purchase_invoice(
        business_unit_id=test_business_unit.id,
        supplier_id=alpha_supplier.id,
        invoice_number="INV-2026-100",
        invoice_date=date(2026, 4, 22),
        currency="HUF",
        gross_total=Decimal("1200.00"),
        lines=[
            {
                "description": "Alpha line",
                "quantity": Decimal("1.000"),
                "uom_id": test_unit_of_measure.id,
                "unit_net_amount": Decimal("1000.00"),
                "line_net_amount": Decimal("1000.00"),
            }
        ],
    )
    create_purchase_invoice(
        business_unit_id=test_business_unit.id,
        supplier_id=beta_supplier.id,
        invoice_number="INV-2026-200",
        invoice_date=date(2026, 4, 23),
        currency="HUF",
        gross_total=Decimal("2400.00"),
        lines=[
            {
                "description": "Beta line",
                "quantity": Decimal("2.000"),
                "uom_id": test_unit_of_measure.id,
                "unit_net_amount": Decimal("1000.00"),
                "line_net_amount": Decimal("2000.00"),
            }
        ],
    )

    response = client.get(
        f"{API_PREFIX}/purchase-invoices",
        params={
            "business_unit_id": str(test_business_unit.id),
            "supplier_id": str(beta_supplier.id),
            "limit": 1,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["supplier_id"] == str(beta_supplier.id)
    assert payload[0]["invoice_number"] == "INV-2026-200"
    assert payload[0]["invoice_date"] == "2026-04-23"
