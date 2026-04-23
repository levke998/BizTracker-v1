"""Integration tests for inventory movement write API."""

from __future__ import annotations

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
