"""Integration tests for inventory stock level read API."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from fastapi.testclient import TestClient

from app.modules.master_data.infrastructure.orm.business_unit_model import (
    BusinessUnitModel,
)
from app.modules.master_data.infrastructure.orm.unit_of_measure_model import (
    UnitOfMeasureModel,
)

API_PREFIX = "/api/v1/inventory"


def test_list_inventory_stock_levels_returns_successful_result(
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
    create_inventory_movement(
        business_unit_id=test_business_unit.id,
        inventory_item_id=item.id,
        movement_type="purchase",
        quantity=Decimal("10.000"),
        uom_id=test_unit_of_measure.id,
        unit_cost=Decimal("100.00"),
        occurred_at=datetime(2026, 4, 23, 10, 0, tzinfo=UTC),
    )

    response = client.get(
        f"{API_PREFIX}/stock-levels",
        params={"business_unit_id": str(test_business_unit.id)},
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["inventory_item_id"] == str(item.id)
    assert payload[0]["name"] == "Flour"
    assert payload[0]["current_quantity"] == "10.000"
    assert payload[0]["movement_count"] == 1


def test_list_inventory_stock_levels_filters_by_business_unit(
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
    create_inventory_item(
        business_unit_id=gourmand_business_unit.id,
        uom_id=test_unit_of_measure.id,
        name=f"Other Unit Item {datetime.now(UTC).timestamp()}",
        item_type="raw_material",
    )
    create_inventory_movement(
        business_unit_id=test_business_unit.id,
        inventory_item_id=item.id,
        movement_type="initial_stock",
        quantity=Decimal("3.000"),
        uom_id=test_unit_of_measure.id,
        occurred_at=datetime(2026, 4, 23, 10, 0, tzinfo=UTC),
    )

    response = client.get(
        f"{API_PREFIX}/stock-levels",
        params={"business_unit_id": str(test_business_unit.id)},
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["business_unit_id"] == str(test_business_unit.id)


def test_list_inventory_stock_levels_filters_by_inventory_item_id(
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
        unit_cost=Decimal("150.00"),
        occurred_at=datetime(2026, 4, 23, 9, 0, tzinfo=UTC),
    )
    create_inventory_movement(
        business_unit_id=test_business_unit.id,
        inventory_item_id=butter_item.id,
        movement_type="purchase",
        quantity=Decimal("2.000"),
        uom_id=test_unit_of_measure.id,
        unit_cost=Decimal("200.00"),
        occurred_at=datetime(2026, 4, 23, 10, 0, tzinfo=UTC),
    )

    response = client.get(
        f"{API_PREFIX}/stock-levels",
        params={
            "business_unit_id": str(test_business_unit.id),
            "inventory_item_id": str(butter_item.id),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["inventory_item_id"] == str(butter_item.id)


def test_list_inventory_stock_levels_filters_by_item_type(
    client: TestClient,
    create_inventory_item,
    create_inventory_movement,
    test_business_unit: BusinessUnitModel,
    test_unit_of_measure: UnitOfMeasureModel,
) -> None:
    raw_item = create_inventory_item(
        business_unit_id=test_business_unit.id,
        uom_id=test_unit_of_measure.id,
        name="Butter",
        item_type="raw_material",
    )
    packaging_item = create_inventory_item(
        business_unit_id=test_business_unit.id,
        uom_id=test_unit_of_measure.id,
        name="Cake Box",
        item_type="packaging",
    )
    create_inventory_movement(
        business_unit_id=test_business_unit.id,
        inventory_item_id=raw_item.id,
        movement_type="purchase",
        quantity=Decimal("2.000"),
        uom_id=test_unit_of_measure.id,
        unit_cost=Decimal("200.00"),
        occurred_at=datetime(2026, 4, 23, 10, 0, tzinfo=UTC),
    )
    create_inventory_movement(
        business_unit_id=test_business_unit.id,
        inventory_item_id=packaging_item.id,
        movement_type="adjustment",
        quantity=Decimal("4.000"),
        uom_id=test_unit_of_measure.id,
        occurred_at=datetime(2026, 4, 23, 11, 0, tzinfo=UTC),
    )

    response = client.get(
        f"{API_PREFIX}/stock-levels",
        params={
            "business_unit_id": str(test_business_unit.id),
            "item_type": "packaging",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["item_type"] == "packaging"
    assert payload[0]["name"] == "Cake Box"


def test_list_inventory_stock_levels_are_sorted_by_name_asc(
    client: TestClient,
    create_inventory_item,
    test_business_unit: BusinessUnitModel,
    test_unit_of_measure: UnitOfMeasureModel,
) -> None:
    create_inventory_item(
        business_unit_id=test_business_unit.id,
        uom_id=test_unit_of_measure.id,
        name="Yeast",
        item_type="raw_material",
    )
    create_inventory_item(
        business_unit_id=test_business_unit.id,
        uom_id=test_unit_of_measure.id,
        name="Butter",
        item_type="raw_material",
    )

    response = client.get(
        f"{API_PREFIX}/stock-levels",
        params={"business_unit_id": str(test_business_unit.id)},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload[0]["name"] == "Butter"
    assert payload[1]["name"] == "Yeast"


def test_list_inventory_stock_levels_respects_limit(
    client: TestClient,
    create_inventory_item,
    test_business_unit: BusinessUnitModel,
    test_unit_of_measure: UnitOfMeasureModel,
) -> None:
    for name in ["Apple", "Banana", "Cherry"]:
        create_inventory_item(
            business_unit_id=test_business_unit.id,
            uom_id=test_unit_of_measure.id,
            name=name,
            item_type="raw_material",
        )

    response = client.get(
        f"{API_PREFIX}/stock-levels",
        params={"business_unit_id": str(test_business_unit.id), "limit": 2},
    )

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_list_inventory_stock_levels_calculates_quantity_from_mixed_movements(
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
        movement_type="initial_stock",
        quantity=Decimal("5.000"),
        uom_id=test_unit_of_measure.id,
        occurred_at=datetime(2026, 4, 23, 8, 0, tzinfo=UTC),
    )
    create_inventory_movement(
        business_unit_id=test_business_unit.id,
        inventory_item_id=item.id,
        movement_type="purchase",
        quantity=Decimal("10.000"),
        uom_id=test_unit_of_measure.id,
        unit_cost=Decimal("180.00"),
        occurred_at=datetime(2026, 4, 23, 9, 0, tzinfo=UTC),
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
        business_unit_id=test_business_unit.id,
        inventory_item_id=item.id,
        movement_type="waste",
        quantity=Decimal("1.500"),
        uom_id=test_unit_of_measure.id,
        occurred_at=datetime(2026, 4, 23, 11, 0, tzinfo=UTC),
    )

    response = client.get(
        f"{API_PREFIX}/stock-levels",
        params={
            "business_unit_id": str(test_business_unit.id),
            "inventory_item_id": str(item.id),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["current_quantity"] == "15.500"
    assert payload[0]["movement_count"] == 4
    last_movement_at = datetime.fromisoformat(
        payload[0]["last_movement_at"].replace("Z", "+00:00")
    ).astimezone(UTC)
    assert last_movement_at == datetime(2026, 4, 23, 11, 0, tzinfo=UTC)
