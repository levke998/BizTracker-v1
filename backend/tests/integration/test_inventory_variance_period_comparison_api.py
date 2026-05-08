"""Integration tests for inventory variance period comparison API."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.modules.master_data.infrastructure.orm.business_unit_model import (
    BusinessUnitModel,
)
from app.modules.master_data.infrastructure.orm.unit_of_measure_model import (
    UnitOfMeasureModel,
)
from app.modules.inventory.infrastructure.orm.inventory_variance_threshold_model import (
    InventoryVarianceThresholdModel,
)

API_PREFIX = "/api/v1/inventory"


def test_variance_period_comparison_flags_worsening_loss(
    client: TestClient,
    db_session: Session,
    create_inventory_item,
    create_inventory_movement,
    test_business_unit: BusinessUnitModel,
    test_unit_of_measure: UnitOfMeasureModel,
) -> None:
    now = datetime.now(UTC)
    item = create_inventory_item(
        business_unit_id=test_business_unit.id,
        uom_id=test_unit_of_measure.id,
        name="Variance Compare Flour",
        item_type="raw_material",
    )
    item.default_unit_cost = Decimal("1000.00")
    db_session.commit()
    previous = create_inventory_movement(
        business_unit_id=test_business_unit.id,
        inventory_item_id=item.id,
        movement_type="waste",
        quantity=Decimal("1.000"),
        uom_id=test_unit_of_measure.id,
        occurred_at=now - timedelta(days=40),
    )
    current = create_inventory_movement(
        business_unit_id=test_business_unit.id,
        inventory_item_id=item.id,
        movement_type="waste",
        quantity=Decimal("2.000"),
        uom_id=test_unit_of_measure.id,
        occurred_at=now - timedelta(days=5),
    )
    previous.reason_code = "waste"
    current.reason_code = "waste"
    db_session.commit()

    response = client.get(
        f"{API_PREFIX}/variance-period-comparison",
        params={
            "business_unit_id": str(test_business_unit.id),
            "inventory_item_id": str(item.id),
            "days": 30,
            "high_loss_value_threshold": "5000",
            "worsening_percent_threshold": "25",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["period_days"] == 30
    assert payload["current_movement_count"] == 1
    assert payload["previous_movement_count"] == 1
    assert payload["movement_count_change"] == 0
    assert payload["current_shortage_quantity"] == "2.000"
    assert payload["previous_shortage_quantity"] == "1.000"
    assert payload["current_estimated_shortage_value"] == "2000.00"
    assert payload["previous_estimated_shortage_value"] == "1000.00"
    assert payload["estimated_shortage_value_change"] == "1000.00"
    assert payload["estimated_shortage_value_change_percent"] == "100.00"
    assert payload["decision_status"] == "worsening"
    assert payload["recommendation"]


def test_variance_period_comparison_flags_missing_cost(
    client: TestClient,
    db_session: Session,
    create_inventory_item,
    create_inventory_movement,
    test_business_unit: BusinessUnitModel,
    test_unit_of_measure: UnitOfMeasureModel,
) -> None:
    item = create_inventory_item(
        business_unit_id=test_business_unit.id,
        uom_id=test_unit_of_measure.id,
        name="Variance Compare Missing Cost",
        item_type="raw_material",
    )
    movement = create_inventory_movement(
        business_unit_id=test_business_unit.id,
        inventory_item_id=item.id,
        movement_type="waste",
        quantity=Decimal("1.000"),
        uom_id=test_unit_of_measure.id,
        occurred_at=datetime.now(UTC) - timedelta(days=2),
    )
    movement.reason_code = "waste"
    db_session.commit()

    response = client.get(
        f"{API_PREFIX}/variance-period-comparison",
        params={
            "business_unit_id": str(test_business_unit.id),
            "inventory_item_id": str(item.id),
            "days": 30,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["current_missing_cost_movement_count"] == 1
    assert payload["decision_status"] == "missing_cost"


def test_variance_thresholds_are_persisted_and_used_by_period_comparison(
    client: TestClient,
    db_session: Session,
    create_inventory_item,
    create_inventory_movement,
    test_business_unit: BusinessUnitModel,
    test_unit_of_measure: UnitOfMeasureModel,
) -> None:
    db_session.execute(
        delete(InventoryVarianceThresholdModel).where(
            InventoryVarianceThresholdModel.business_unit_id == test_business_unit.id
        )
    )
    db_session.commit()

    default_response = client.get(
        f"{API_PREFIX}/variance-thresholds",
        params={"business_unit_id": str(test_business_unit.id)},
    )
    assert default_response.status_code == 200
    assert default_response.json()["is_default"] is True
    assert default_response.json()["high_loss_value_threshold"] == "10000"

    threshold_response = client.put(
        f"{API_PREFIX}/variance-thresholds",
        json={
            "business_unit_id": str(test_business_unit.id),
            "high_loss_value_threshold": "1500.00",
            "worsening_percent_threshold": "50.00",
        },
    )
    assert threshold_response.status_code == 200
    threshold_payload = threshold_response.json()
    assert threshold_payload["is_default"] is False
    assert threshold_payload["high_loss_value_threshold"] == "1500.00"
    assert threshold_payload["worsening_percent_threshold"] == "50.00"

    now = datetime.now(UTC)
    item = create_inventory_item(
        business_unit_id=test_business_unit.id,
        uom_id=test_unit_of_measure.id,
        name="Variance Threshold Flour",
        item_type="raw_material",
    )
    item.default_unit_cost = Decimal("1000.00")
    db_session.commit()
    current = create_inventory_movement(
        business_unit_id=test_business_unit.id,
        inventory_item_id=item.id,
        movement_type="waste",
        quantity=Decimal("2.000"),
        uom_id=test_unit_of_measure.id,
        occurred_at=now - timedelta(days=3),
    )
    current.reason_code = "waste"
    db_session.commit()

    comparison_response = client.get(
        f"{API_PREFIX}/variance-period-comparison",
        params={
            "business_unit_id": str(test_business_unit.id),
            "inventory_item_id": str(item.id),
            "days": 30,
        },
    )

    assert comparison_response.status_code == 200
    assert comparison_response.json()["current_estimated_shortage_value"] == "2000.00"
    assert comparison_response.json()["decision_status"] == "critical"
    db_session.execute(
        delete(InventoryVarianceThresholdModel).where(
            InventoryVarianceThresholdModel.business_unit_id == test_business_unit.id
        )
    )
    db_session.commit()
