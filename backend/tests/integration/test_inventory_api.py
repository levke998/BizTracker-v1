"""Integration tests for inventory read APIs."""

from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from app.modules.master_data.infrastructure.orm.business_unit_model import (
    BusinessUnitModel,
)
from app.modules.master_data.infrastructure.orm.unit_of_measure_model import (
    UnitOfMeasureModel,
)

API_PREFIX = "/api/v1/inventory"


def test_create_inventory_item_succeeds(
    client: TestClient,
    test_business_unit: BusinessUnitModel,
    test_unit_of_measure: UnitOfMeasureModel,
) -> None:
    response = client.post(
        f"{API_PREFIX}/items",
        json={
            "business_unit_id": str(test_business_unit.id),
            "name": "Vanilla Sugar",
            "item_type": "raw_material",
            "uom_id": str(test_unit_of_measure.id),
            "track_stock": True,
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["business_unit_id"] == str(test_business_unit.id)
    assert payload["name"] == "Vanilla Sugar"
    assert payload["item_type"] == "raw_material"
    assert payload["uom_id"] == str(test_unit_of_measure.id)
    assert payload["track_stock"] is True
    assert payload["is_active"] is True


def test_create_inventory_item_with_invalid_business_unit_returns_not_found(
    client: TestClient,
    test_unit_of_measure: UnitOfMeasureModel,
) -> None:
    response = client.post(
        f"{API_PREFIX}/items",
        json={
            "business_unit_id": str(uuid4()),
            "name": "Brown Sugar",
            "item_type": "raw_material",
            "uom_id": str(test_unit_of_measure.id),
            "track_stock": True,
        },
    )

    assert response.status_code == 404
    assert "Business unit" in response.json()["detail"]


def test_create_inventory_item_with_invalid_uom_returns_not_found(
    client: TestClient,
    test_business_unit: BusinessUnitModel,
) -> None:
    response = client.post(
        f"{API_PREFIX}/items",
        json={
            "business_unit_id": str(test_business_unit.id),
            "name": "Salt",
            "item_type": "raw_material",
            "uom_id": str(uuid4()),
            "track_stock": True,
        },
    )

    assert response.status_code == 404
    assert "Unit of measure" in response.json()["detail"]


def test_create_inventory_item_rejects_duplicate_name_in_same_business_unit(
    client: TestClient,
    test_business_unit: BusinessUnitModel,
    test_unit_of_measure: UnitOfMeasureModel,
) -> None:
    payload = {
        "business_unit_id": str(test_business_unit.id),
        "name": "Shared Demo Item",
        "item_type": "packaging",
        "uom_id": str(test_unit_of_measure.id),
        "track_stock": True,
    }

    first_response = client.post(f"{API_PREFIX}/items", json=payload)
    assert first_response.status_code == 201

    second_response = client.post(f"{API_PREFIX}/items", json=payload)

    assert second_response.status_code == 409
    assert "same name already exists" in second_response.json()["detail"]


def test_create_inventory_item_allows_same_name_in_different_business_units(
    client: TestClient,
    test_business_unit: BusinessUnitModel,
    gourmand_business_unit: BusinessUnitModel,
    pcs_unit_of_measure: UnitOfMeasureModel,
) -> None:
    shared_name = "Reusable Demo Item"

    first_response = client.post(
        f"{API_PREFIX}/items",
        json={
            "business_unit_id": str(test_business_unit.id),
            "name": shared_name,
            "item_type": "finished_good",
            "uom_id": str(pcs_unit_of_measure.id),
            "track_stock": True,
        },
    )
    second_response = client.post(
        f"{API_PREFIX}/items",
        json={
            "business_unit_id": str(gourmand_business_unit.id),
            "name": shared_name,
            "item_type": "finished_good",
            "uom_id": str(pcs_unit_of_measure.id),
            "track_stock": True,
        },
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201
    assert first_response.json()["business_unit_id"] != second_response.json()["business_unit_id"]


def test_list_inventory_items_returns_successful_result(
    client: TestClient,
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

    response = client.get(
        f"{API_PREFIX}/items",
        params={"business_unit_id": str(test_business_unit.id)},
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["id"] == str(item.id)
    assert payload[0]["business_unit_id"] == str(test_business_unit.id)
    assert payload[0]["name"] == "Flour"
    assert payload[0]["item_type"] == "raw_material"
    assert payload[0]["uom_id"] == str(test_unit_of_measure.id)
    assert payload[0]["track_stock"] is True
    assert payload[0]["is_active"] is True


def test_list_inventory_items_filters_by_business_unit(
    client: TestClient,
    create_inventory_item,
    test_business_unit: BusinessUnitModel,
    test_unit_of_measure: UnitOfMeasureModel,
) -> None:
    create_inventory_item(
        business_unit_id=test_business_unit.id,
        uom_id=test_unit_of_measure.id,
        name="Sugar",
        item_type="raw_material",
    )

    response = client.get(
        f"{API_PREFIX}/items",
        params={"business_unit_id": str(test_business_unit.id)},
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["business_unit_id"] == str(test_business_unit.id)

    empty_response = client.get(
        f"{API_PREFIX}/items",
        params={"business_unit_id": "00000000-0000-0000-0000-000000000001"},
    )

    assert empty_response.status_code == 200
    assert empty_response.json() == []


def test_list_inventory_items_filters_by_item_type(
    client: TestClient,
    create_inventory_item,
    test_business_unit: BusinessUnitModel,
    test_unit_of_measure: UnitOfMeasureModel,
) -> None:
    create_inventory_item(
        business_unit_id=test_business_unit.id,
        uom_id=test_unit_of_measure.id,
        name="Butter",
        item_type="raw_material",
    )
    create_inventory_item(
        business_unit_id=test_business_unit.id,
        uom_id=test_unit_of_measure.id,
        name="Cake Box",
        item_type="packaging",
    )

    response = client.get(
        f"{API_PREFIX}/items",
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


def test_list_inventory_items_are_sorted_by_name_asc(
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
        f"{API_PREFIX}/items",
        params={"business_unit_id": str(test_business_unit.id)},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload[0]["name"] == "Butter"
    assert payload[1]["name"] == "Yeast"


def test_list_inventory_items_respects_limit(
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
        f"{API_PREFIX}/items",
        params={"business_unit_id": str(test_business_unit.id), "limit": 2},
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 2
