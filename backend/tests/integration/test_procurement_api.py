"""Integration tests for procurement supplier APIs."""

from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from app.modules.master_data.infrastructure.orm.business_unit_model import (
    BusinessUnitModel,
)

API_PREFIX = "/api/v1/procurement"


def test_create_supplier_succeeds(
    client: TestClient,
    test_business_unit: BusinessUnitModel,
) -> None:
    response = client.post(
        f"{API_PREFIX}/suppliers",
        json={
            "business_unit_id": str(test_business_unit.id),
            "name": "Best Flour Kft",
            "tax_id": "12345678-2-42",
            "contact_name": "Anna Teszt",
            "email": "anna@example.com",
            "phone": "+361234567",
            "notes": "Primary dry goods supplier",
            "is_active": True,
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["business_unit_id"] == str(test_business_unit.id)
    assert payload["name"] == "Best Flour Kft"
    assert payload["tax_id"] == "12345678-2-42"
    assert payload["is_active"] is True


def test_create_supplier_with_invalid_business_unit_returns_not_found(
    client: TestClient,
) -> None:
    response = client.post(
        f"{API_PREFIX}/suppliers",
        json={
            "business_unit_id": str(uuid4()),
            "name": "Ghost Supplier",
            "is_active": True,
        },
    )

    assert response.status_code == 404
    assert "Business unit" in response.json()["detail"]


def test_create_supplier_rejects_duplicate_name_in_same_business_unit(
    client: TestClient,
    test_business_unit: BusinessUnitModel,
) -> None:
    payload = {
        "business_unit_id": str(test_business_unit.id),
        "name": "Shared Supplier",
        "is_active": True,
    }

    first_response = client.post(f"{API_PREFIX}/suppliers", json=payload)
    assert first_response.status_code == 201

    second_response = client.post(f"{API_PREFIX}/suppliers", json=payload)

    assert second_response.status_code == 409
    assert "same name already exists" in second_response.json()["detail"]


def test_list_suppliers_returns_successful_result(
    client: TestClient,
    create_supplier,
    test_business_unit: BusinessUnitModel,
) -> None:
    supplier = create_supplier(
        business_unit_id=test_business_unit.id,
        name="Warehouse Drinks",
        is_active=True,
    )

    response = client.get(
        f"{API_PREFIX}/suppliers",
        params={"business_unit_id": str(test_business_unit.id)},
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["id"] == str(supplier.id)
    assert payload[0]["name"] == "Warehouse Drinks"


def test_list_suppliers_filters_by_is_active(
    client: TestClient,
    create_supplier,
    test_business_unit: BusinessUnitModel,
) -> None:
    create_supplier(
        business_unit_id=test_business_unit.id,
        name="Active Supplier",
        is_active=True,
    )
    create_supplier(
        business_unit_id=test_business_unit.id,
        name="Archived Supplier",
        is_active=False,
    )

    response = client.get(
        f"{API_PREFIX}/suppliers",
        params={
            "business_unit_id": str(test_business_unit.id),
            "is_active": "true",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["name"] == "Active Supplier"
    assert payload[0]["is_active"] is True


def test_list_suppliers_are_sorted_by_name_asc(
    client: TestClient,
    create_supplier,
    test_business_unit: BusinessUnitModel,
) -> None:
    create_supplier(
        business_unit_id=test_business_unit.id,
        name="Zeta Supplier",
    )
    create_supplier(
        business_unit_id=test_business_unit.id,
        name="Alpha Supplier",
    )

    response = client.get(
        f"{API_PREFIX}/suppliers",
        params={"business_unit_id": str(test_business_unit.id)},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload[0]["name"] == "Alpha Supplier"
    assert payload[1]["name"] == "Zeta Supplier"


def test_list_suppliers_respects_limit(
    client: TestClient,
    create_supplier,
    test_business_unit: BusinessUnitModel,
) -> None:
    for name in ["Alpha", "Beta", "Gamma"]:
        create_supplier(
            business_unit_id=test_business_unit.id,
            name=f"{name} Supplier",
        )

    response = client.get(
        f"{API_PREFIX}/suppliers",
        params={"business_unit_id": str(test_business_unit.id), "limit": 2},
    )

    assert response.status_code == 200
    assert len(response.json()) == 2
