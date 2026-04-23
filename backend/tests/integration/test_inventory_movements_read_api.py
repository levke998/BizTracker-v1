"""Integration tests for inventory movement read API."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient

from app.modules.master_data.infrastructure.orm.business_unit_model import (
    BusinessUnitModel,
)
from app.modules.master_data.infrastructure.orm.unit_of_measure_model import (
    UnitOfMeasureModel,
)

API_PREFIX = "/api/v1/inventory"


def test_list_inventory_movements_returns_successful_result(
    client: TestClient,
    create_inventory_item,
    create_inventory_movement,
    test_business_unit: BusinessUnitModel,
    test_unit_of_measure: UnitOfMeasureModel,
) -> None:
    item = create_inventory_item(
        business_unit_id=test_business_unit.id,
        uom_id=test_unit_of_measure.id,
        name="Flour",
        item_type="raw_material",
    )
    movement = create_inventory_movement(
        business_unit_id=test_business_unit.id,
        inventory_item_id=item.id,
        movement_type="purchase",
        quantity=Decimal("10.000"),
        uom_id=test_unit_of_measure.id,
        unit_cost=Decimal("100.00"),
        note="Supplier delivery",
        occurred_at=datetime(2026, 4, 23, 10, 0, tzinfo=UTC),
    )

    response = client.get(
        f"{API_PREFIX}/movements",
        params={"business_unit_id": str(test_business_unit.id)},
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["id"] == str(movement.id)
    assert payload[0]["inventory_item_id"] == str(item.id)
    assert payload[0]["movement_type"] == "purchase"
    assert payload[0]["quantity"] == "10.000"
    assert payload[0]["unit_cost"] == "100.00"
    assert payload[0]["note"] == "Supplier delivery"


def test_list_inventory_movements_filters_by_business_unit(
    client: TestClient,
    create_inventory_item,
    create_inventory_movement,
    test_business_unit: BusinessUnitModel,
    gourmand_business_unit: BusinessUnitModel,
    test_unit_of_measure: UnitOfMeasureModel,
) -> None:
    item = create_inventory_item(
        business_unit_id=test_business_unit.id,
        uom_id=test_unit_of_measure.id,
        name="Sugar",
        item_type="raw_material",
    )
    other_item = create_inventory_item(
        business_unit_id=gourmand_business_unit.id,
        uom_id=test_unit_of_measure.id,
        name=f"Gourmand Read Item {uuid4().hex[:8]}",
        item_type="raw_material",
    )
    create_inventory_movement(
        business_unit_id=test_business_unit.id,
        inventory_item_id=item.id,
        movement_type="adjustment",
        quantity=Decimal("2.000"),
        uom_id=test_unit_of_measure.id,
        occurred_at=datetime(2026, 4, 23, 10, 0, tzinfo=UTC),
    )
    create_inventory_movement(
        business_unit_id=gourmand_business_unit.id,
        inventory_item_id=other_item.id,
        movement_type="adjustment",
        quantity=Decimal("1.000"),
        uom_id=test_unit_of_measure.id,
        occurred_at=datetime(2026, 4, 23, 11, 0, tzinfo=UTC),
    )

    response = client.get(
        f"{API_PREFIX}/movements",
        params={"business_unit_id": str(test_business_unit.id)},
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["business_unit_id"] == str(test_business_unit.id)


def test_list_inventory_movements_filters_by_inventory_item_id(
    client: TestClient,
    create_inventory_item,
    create_inventory_movement,
    test_business_unit: BusinessUnitModel,
    test_unit_of_measure: UnitOfMeasureModel,
) -> None:
    flour_item = create_inventory_item(
        business_unit_id=test_business_unit.id,
        uom_id=test_unit_of_measure.id,
        name="Flour",
        item_type="raw_material",
    )
    butter_item = create_inventory_item(
        business_unit_id=test_business_unit.id,
        uom_id=test_unit_of_measure.id,
        name="Butter",
        item_type="raw_material",
    )
    create_inventory_movement(
        business_unit_id=test_business_unit.id,
        inventory_item_id=flour_item.id,
        movement_type="purchase",
        quantity=Decimal("5.000"),
        uom_id=test_unit_of_measure.id,
        unit_cost=Decimal("90.00"),
        occurred_at=datetime(2026, 4, 23, 9, 0, tzinfo=UTC),
    )
    target = create_inventory_movement(
        business_unit_id=test_business_unit.id,
        inventory_item_id=butter_item.id,
        movement_type="waste",
        quantity=Decimal("1.000"),
        uom_id=test_unit_of_measure.id,
        occurred_at=datetime(2026, 4, 23, 10, 0, tzinfo=UTC),
    )

    response = client.get(
        f"{API_PREFIX}/movements",
        params={
            "business_unit_id": str(test_business_unit.id),
            "inventory_item_id": str(butter_item.id),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["id"] == str(target.id)


def test_list_inventory_movements_filters_by_movement_type(
    client: TestClient,
    create_inventory_item,
    create_inventory_movement,
    test_business_unit: BusinessUnitModel,
    test_unit_of_measure: UnitOfMeasureModel,
) -> None:
    item = create_inventory_item(
        business_unit_id=test_business_unit.id,
        uom_id=test_unit_of_measure.id,
        name="Milk",
        item_type="raw_material",
    )
    create_inventory_movement(
        business_unit_id=test_business_unit.id,
        inventory_item_id=item.id,
        movement_type="purchase",
        quantity=Decimal("3.000"),
        uom_id=test_unit_of_measure.id,
        unit_cost=Decimal("120.00"),
        occurred_at=datetime(2026, 4, 23, 9, 0, tzinfo=UTC),
    )
    create_inventory_movement(
        business_unit_id=test_business_unit.id,
        inventory_item_id=item.id,
        movement_type="waste",
        quantity=Decimal("1.000"),
        uom_id=test_unit_of_measure.id,
        occurred_at=datetime(2026, 4, 23, 10, 0, tzinfo=UTC),
    )

    response = client.get(
        f"{API_PREFIX}/movements",
        params={
            "business_unit_id": str(test_business_unit.id),
            "movement_type": "waste",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["movement_type"] == "waste"


def test_list_inventory_movements_are_sorted_by_occurred_at_desc(
    client: TestClient,
    create_inventory_item,
    create_inventory_movement,
    test_business_unit: BusinessUnitModel,
    test_unit_of_measure: UnitOfMeasureModel,
) -> None:
    item = create_inventory_item(
        business_unit_id=test_business_unit.id,
        uom_id=test_unit_of_measure.id,
        name="Packaging",
        item_type="packaging",
    )
    create_inventory_movement(
        business_unit_id=test_business_unit.id,
        inventory_item_id=item.id,
        movement_type="initial_stock",
        quantity=Decimal("4.000"),
        uom_id=test_unit_of_measure.id,
        occurred_at=datetime(2026, 4, 23, 8, 0, tzinfo=UTC),
    )
    newer = create_inventory_movement(
        business_unit_id=test_business_unit.id,
        inventory_item_id=item.id,
        movement_type="adjustment",
        quantity=Decimal("1.000"),
        uom_id=test_unit_of_measure.id,
        occurred_at=datetime(2026, 4, 23, 12, 0, tzinfo=UTC),
    )

    response = client.get(
        f"{API_PREFIX}/movements",
        params={"business_unit_id": str(test_business_unit.id)},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload[0]["id"] == str(newer.id)


def test_list_inventory_movements_respects_limit(
    client: TestClient,
    create_inventory_item,
    create_inventory_movement,
    test_business_unit: BusinessUnitModel,
    test_unit_of_measure: UnitOfMeasureModel,
) -> None:
    item = create_inventory_item(
        business_unit_id=test_business_unit.id,
        uom_id=test_unit_of_measure.id,
        name="Coffee Beans",
        item_type="raw_material",
    )
    for index in range(3):
        create_inventory_movement(
            business_unit_id=test_business_unit.id,
            inventory_item_id=item.id,
            movement_type="adjustment",
            quantity=Decimal("1.000"),
            uom_id=test_unit_of_measure.id,
            occurred_at=datetime(2026, 4, 23, 10 + index, 0, tzinfo=UTC),
        )

    response = client.get(
        f"{API_PREFIX}/movements",
        params={"business_unit_id": str(test_business_unit.id), "limit": 2},
    )

    assert response.status_code == 200
    assert len(response.json()) == 2
