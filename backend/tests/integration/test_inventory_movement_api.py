"""Integration tests for inventory movement write API."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient

from app.modules.inventory.infrastructure.orm.inventory_movement_model import (
    InventoryMovementModel,
)
from app.modules.master_data.infrastructure.orm.business_unit_model import (
    BusinessUnitModel,
)
from app.modules.master_data.infrastructure.orm.unit_of_measure_model import (
    UnitOfMeasureModel,
)

API_PREFIX = "/api/v1/inventory"


def test_create_purchase_movement_succeeds(
    client: TestClient,
    db_session,
    create_inventory_item,
    test_business_unit: BusinessUnitModel,
    test_unit_of_measure: UnitOfMeasureModel,
) -> None:
    item = create_inventory_item(
        business_unit_id=test_business_unit.id,
        uom_id=test_unit_of_measure.id,
        name="Flour",
        item_type="raw_material",
    )

    response = client.post(
        f"{API_PREFIX}/movements",
        json={
            "business_unit_id": str(test_business_unit.id),
            "inventory_item_id": str(item.id),
            "movement_type": "purchase",
            "quantity": "12.5",
            "uom_id": str(test_unit_of_measure.id),
            "unit_cost": "435.50",
            "note": "Supplier delivery",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["business_unit_id"] == str(test_business_unit.id)
    assert payload["inventory_item_id"] == str(item.id)
    assert payload["movement_type"] == "purchase"
    assert payload["quantity"] == "12.500"
    assert payload["uom_id"] == str(test_unit_of_measure.id)
    assert payload["unit_cost"] == "435.50"
    assert payload["occurred_at"]
    assert payload["created_at"]

    movement = db_session.get(InventoryMovementModel, payload["id"])
    assert movement is not None
    assert movement.note == "Supplier delivery"


def test_create_adjustment_movement_succeeds_without_unit_cost(
    client: TestClient,
    create_inventory_item,
    test_business_unit: BusinessUnitModel,
    test_unit_of_measure: UnitOfMeasureModel,
) -> None:
    item = create_inventory_item(
        business_unit_id=test_business_unit.id,
        uom_id=test_unit_of_measure.id,
        name="Cake Box",
        item_type="packaging",
    )

    response = client.post(
        f"{API_PREFIX}/movements",
        json={
            "business_unit_id": str(test_business_unit.id),
            "inventory_item_id": str(item.id),
            "movement_type": "adjustment",
            "quantity": "3",
            "uom_id": str(test_unit_of_measure.id),
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["movement_type"] == "adjustment"
    assert payload["unit_cost"] is None


def test_register_physical_stock_count_creates_shortage_correction(
    client: TestClient,
    create_inventory_item,
    create_inventory_movement,
    test_business_unit: BusinessUnitModel,
    test_unit_of_measure: UnitOfMeasureModel,
) -> None:
    item = create_inventory_item(
        business_unit_id=test_business_unit.id,
        uom_id=test_unit_of_measure.id,
        name="Physical Count Flour",
        item_type="raw_material",
    )
    create_inventory_movement(
        business_unit_id=test_business_unit.id,
        inventory_item_id=item.id,
        movement_type="purchase",
        quantity=Decimal("12.000"),
        uom_id=test_unit_of_measure.id,
        unit_cost=Decimal("100.00"),
        occurred_at=datetime(2026, 5, 7, 8, 0, tzinfo=UTC),
    )

    response = client.post(
        f"{API_PREFIX}/physical-stock-counts",
        json={
            "business_unit_id": str(test_business_unit.id),
            "inventory_item_id": str(item.id),
            "counted_quantity": "7",
            "uom_id": str(test_unit_of_measure.id),
            "reason_code": "breakage",
            "note": "Physical count after prep",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["previous_quantity"] == "12.000"
    assert payload["counted_quantity"] == "7.000"
    assert payload["adjustment_quantity"] == "-5.000"
    assert payload["movement"]["movement_type"] == "waste"
    assert payload["movement"]["quantity"] == "5.000"
    assert payload["movement"]["reason_code"] == "breakage"
    assert payload["movement"]["source_type"] == "physical_stock_count"

    stock_response = client.get(
        f"{API_PREFIX}/stock-levels",
        params={"inventory_item_id": str(item.id)},
    )
    assert stock_response.status_code == 200
    assert stock_response.json()[0]["current_quantity"] == "7.000"


def test_list_variance_reason_summary_groups_physical_corrections(
    client: TestClient,
    create_inventory_item,
    create_inventory_movement,
    test_business_unit: BusinessUnitModel,
    test_unit_of_measure: UnitOfMeasureModel,
) -> None:
    flour = create_inventory_item(
        business_unit_id=test_business_unit.id,
        uom_id=test_unit_of_measure.id,
        name="Variance Flour",
        item_type="raw_material",
    )
    sugar = create_inventory_item(
        business_unit_id=test_business_unit.id,
        uom_id=test_unit_of_measure.id,
        name="Variance Sugar",
        item_type="raw_material",
    )
    create_inventory_movement(
        business_unit_id=test_business_unit.id,
        inventory_item_id=flour.id,
        movement_type="purchase",
        quantity=Decimal("10.000"),
        uom_id=test_unit_of_measure.id,
        unit_cost=Decimal("100.00"),
        occurred_at=datetime(2026, 5, 7, 8, 0, tzinfo=UTC),
    )
    create_inventory_movement(
        business_unit_id=test_business_unit.id,
        inventory_item_id=sugar.id,
        movement_type="purchase",
        quantity=Decimal("4.000"),
        uom_id=test_unit_of_measure.id,
        unit_cost=Decimal("50.00"),
        occurred_at=datetime(2026, 5, 7, 8, 0, tzinfo=UTC),
    )

    client.post(
        f"{API_PREFIX}/physical-stock-counts",
        json={
            "business_unit_id": str(test_business_unit.id),
            "inventory_item_id": str(flour.id),
            "counted_quantity": "7",
            "uom_id": str(test_unit_of_measure.id),
            "reason_code": "breakage",
        },
    )
    client.post(
        f"{API_PREFIX}/physical-stock-counts",
        json={
            "business_unit_id": str(test_business_unit.id),
            "inventory_item_id": str(sugar.id),
            "counted_quantity": "5",
            "uom_id": str(test_unit_of_measure.id),
            "reason_code": "missing_purchase_invoice",
        },
    )

    response = client.get(
        f"{API_PREFIX}/variance-reasons",
        params={"business_unit_id": str(test_business_unit.id)},
    )

    assert response.status_code == 200
    payload = {row["reason_code"]: row for row in response.json()}
    assert payload["breakage"]["movement_count"] == 1
    assert payload["breakage"]["total_quantity"] == "3.000"
    assert payload["breakage"]["net_quantity_delta"] == "-3.000"
    assert payload["missing_purchase_invoice"]["movement_count"] == 1
    assert payload["missing_purchase_invoice"]["total_quantity"] == "1.000"
    assert payload["missing_purchase_invoice"]["net_quantity_delta"] == "1.000"


def test_list_variance_trend_and_item_summary(
    client: TestClient,
    db_session,
    create_inventory_item,
    create_inventory_movement,
    test_business_unit: BusinessUnitModel,
    test_unit_of_measure: UnitOfMeasureModel,
) -> None:
    flour = create_inventory_item(
        business_unit_id=test_business_unit.id,
        uom_id=test_unit_of_measure.id,
        name="Variance Trend Flour",
        item_type="raw_material",
    )
    sugar = create_inventory_item(
        business_unit_id=test_business_unit.id,
        uom_id=test_unit_of_measure.id,
        name="Variance Trend Sugar",
        item_type="raw_material",
    )
    flour.default_unit_cost = Decimal("100.00")
    sugar.default_unit_cost = Decimal("50.00")
    db_session.commit()
    create_inventory_movement(
        business_unit_id=test_business_unit.id,
        inventory_item_id=flour.id,
        movement_type="purchase",
        quantity=Decimal("10.000"),
        uom_id=test_unit_of_measure.id,
        unit_cost=Decimal("100.00"),
        occurred_at=datetime(2026, 5, 7, 8, 0, tzinfo=UTC),
    )
    create_inventory_movement(
        business_unit_id=test_business_unit.id,
        inventory_item_id=sugar.id,
        movement_type="purchase",
        quantity=Decimal("8.000"),
        uom_id=test_unit_of_measure.id,
        unit_cost=Decimal("50.00"),
        occurred_at=datetime(2026, 5, 7, 8, 0, tzinfo=UTC),
    )

    client.post(
        f"{API_PREFIX}/physical-stock-counts",
        json={
            "business_unit_id": str(test_business_unit.id),
            "inventory_item_id": str(flour.id),
            "counted_quantity": "6",
            "uom_id": str(test_unit_of_measure.id),
            "reason_code": "waste",
            "occurred_at": "2026-05-07T12:00:00Z",
        },
    )
    client.post(
        f"{API_PREFIX}/physical-stock-counts",
        json={
            "business_unit_id": str(test_business_unit.id),
            "inventory_item_id": str(sugar.id),
            "counted_quantity": "10",
            "uom_id": str(test_unit_of_measure.id),
            "reason_code": "missing_purchase_invoice",
            "occurred_at": "2026-05-07T13:00:00Z",
        },
    )

    trend_response = client.get(
        f"{API_PREFIX}/variance-trend",
        params={"business_unit_id": str(test_business_unit.id), "days": 365},
    )
    item_response = client.get(
        f"{API_PREFIX}/variance-items",
        params={"business_unit_id": str(test_business_unit.id)},
    )

    assert trend_response.status_code == 200
    trend = trend_response.json()
    assert trend
    assert trend[-1]["movement_count"] >= 2
    assert trend[-1]["shortage_quantity"] == "4.000"
    assert trend[-1]["surplus_quantity"] == "2.000"
    assert trend[-1]["net_quantity_delta"] == "-2.000"
    assert trend[-1]["estimated_shortage_value"] == "400.00"
    assert trend[-1]["estimated_surplus_value"] == "100.00"
    assert trend[-1]["estimated_net_value_delta"] == "-300.00"
    assert trend[-1]["missing_cost_movement_count"] == 0

    assert item_response.status_code == 200
    items = {row["name"]: row for row in item_response.json()}
    assert items["Variance Trend Flour"]["shortage_quantity"] == "4.000"
    assert items["Variance Trend Flour"]["net_quantity_delta"] == "-4.000"
    assert items["Variance Trend Flour"]["default_unit_cost"] == "100.00"
    assert items["Variance Trend Flour"]["estimated_shortage_value"] == "400.00"
    assert items["Variance Trend Flour"]["estimated_net_value_delta"] == "-400.00"
    assert items["Variance Trend Flour"]["anomaly_status"] == "watch"
    assert items["Variance Trend Sugar"]["surplus_quantity"] == "2.000"
    assert items["Variance Trend Sugar"]["net_quantity_delta"] == "2.000"
    assert items["Variance Trend Sugar"]["estimated_surplus_value"] == "100.00"
    assert items["Variance Trend Sugar"]["estimated_net_value_delta"] == "100.00"
    assert items["Variance Trend Sugar"]["anomaly_status"] == "surplus_review"


def test_create_purchase_movement_requires_unit_cost(
    client: TestClient,
    create_inventory_item,
    test_business_unit: BusinessUnitModel,
    test_unit_of_measure: UnitOfMeasureModel,
) -> None:
    item = create_inventory_item(
        business_unit_id=test_business_unit.id,
        uom_id=test_unit_of_measure.id,
        name="Butter",
        item_type="raw_material",
    )

    response = client.post(
        f"{API_PREFIX}/movements",
        json={
            "business_unit_id": str(test_business_unit.id),
            "inventory_item_id": str(item.id),
            "movement_type": "purchase",
            "quantity": "5",
            "uom_id": str(test_unit_of_measure.id),
        },
    )

    assert response.status_code == 422
    assert "unit_cost" in response.json()["detail"]


def test_create_movement_with_invalid_inventory_item_returns_not_found(
    client: TestClient,
    test_business_unit: BusinessUnitModel,
    test_unit_of_measure: UnitOfMeasureModel,
) -> None:
    response = client.post(
        f"{API_PREFIX}/movements",
        json={
            "business_unit_id": str(test_business_unit.id),
            "inventory_item_id": str(uuid4()),
            "movement_type": "adjustment",
            "quantity": "2",
            "uom_id": str(test_unit_of_measure.id),
        },
    )

    assert response.status_code == 404
    assert "Inventory item" in response.json()["detail"]


def test_create_movement_with_non_positive_quantity_returns_validation_error(
    client: TestClient,
    create_inventory_item,
    test_business_unit: BusinessUnitModel,
    test_unit_of_measure: UnitOfMeasureModel,
) -> None:
    item = create_inventory_item(
        business_unit_id=test_business_unit.id,
        uom_id=test_unit_of_measure.id,
        name="Sugar",
        item_type="raw_material",
    )

    response = client.post(
        f"{API_PREFIX}/movements",
        json={
            "business_unit_id": str(test_business_unit.id),
            "inventory_item_id": str(item.id),
            "movement_type": "adjustment",
            "quantity": "0",
            "uom_id": str(test_unit_of_measure.id),
        },
    )

    assert response.status_code == 422
    assert "greater than 0" in str(response.json()["detail"])
