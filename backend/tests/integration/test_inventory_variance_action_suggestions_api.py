"""Integration tests for inventory variance action suggestions API."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.modules.master_data.infrastructure.orm.business_unit_model import (
    BusinessUnitModel,
)
from app.modules.master_data.infrastructure.orm.unit_of_measure_model import (
    UnitOfMeasureModel,
)

API_PREFIX = "/api/v1/inventory"


def test_variance_action_suggestions_prioritize_high_loss_item(
    client: TestClient,
    db_session,
    create_inventory_item,
    create_inventory_movement,
    test_business_unit: BusinessUnitModel,
    test_unit_of_measure: UnitOfMeasureModel,
) -> None:
    item = create_inventory_item(
        business_unit_id=test_business_unit.id,
        uom_id=test_unit_of_measure.id,
        name="Action Suggestion Flour",
        item_type="raw_material",
    )
    item.default_unit_cost = Decimal("5000.00")
    db_session.commit()

    movement = create_inventory_movement(
        business_unit_id=test_business_unit.id,
        inventory_item_id=item.id,
        movement_type="waste",
        quantity=Decimal("3.000"),
        uom_id=test_unit_of_measure.id,
        occurred_at=datetime.now(UTC) - timedelta(days=2),
    )
    movement.reason_code = "waste"
    db_session.commit()

    response = client.get(
        f"{API_PREFIX}/variance-action-suggestions",
        params={"business_unit_id": str(test_business_unit.id), "days": 30},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload
    assert payload[0]["severity"] == "critical"
    assert payload[0]["priority_score"] == 100
    assert {
        "period_critical",
        "investigate_high_loss_item",
    }.intersection({row["action_type"] for row in payload})
    item_suggestion = next(
        row for row in payload if row["action_type"] == "investigate_high_loss_item"
    )
    assert item_suggestion["inventory_item_id"] == str(item.id)
    assert item_suggestion["estimated_impact_value"] == "15000.00"
    assert item_suggestion["action_target_type"] == "inventory_theoretical_stock"
    assert item_suggestion["action_target_label"] == "Fogyasi naplo"
    assert item_suggestion["action_target_params"] == {
        "business_unit_id": str(test_business_unit.id),
        "inventory_item_id": str(item.id),
        "action_suggestion_id": item_suggestion["id"],
    }
    assert item_suggestion["review_status"] == "open"
    assert item_suggestion["reviewed_at"] is None


def test_variance_action_suggestions_returns_routine_monitoring_when_clean(
    client: TestClient,
    test_business_unit: BusinessUnitModel,
) -> None:
    response = client.get(
        f"{API_PREFIX}/variance-action-suggestions",
        params={"business_unit_id": str(test_business_unit.id), "days": 30},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload[0]["action_type"] == "routine_monitoring"
    assert payload[0]["severity"] == "info"


def test_variance_action_suggestions_link_missing_cost_item_to_quick_fix(
    client: TestClient,
    db_session,
    create_inventory_item,
    create_inventory_movement,
    test_business_unit: BusinessUnitModel,
    test_unit_of_measure: UnitOfMeasureModel,
) -> None:
    item = create_inventory_item(
        business_unit_id=test_business_unit.id,
        uom_id=test_unit_of_measure.id,
        name="Missing Cost Quick Fix Flour",
        item_type="raw_material",
    )
    item.default_unit_cost = None
    db_session.commit()

    movement = create_inventory_movement(
        business_unit_id=test_business_unit.id,
        inventory_item_id=item.id,
        movement_type="waste",
        quantity=Decimal("2.000"),
        uom_id=test_unit_of_measure.id,
        occurred_at=datetime.now(UTC) - timedelta(days=2),
    )
    movement.reason_code = "waste"
    db_session.commit()

    response = client.get(
        f"{API_PREFIX}/variance-action-suggestions",
        params={"business_unit_id": str(test_business_unit.id), "days": 30},
    )

    assert response.status_code == 200
    suggestion = next(
        row for row in response.json() if row["action_type"] == "complete_item_cost"
    )
    assert suggestion["action_target_type"] == "catalog_ingredients"
    assert suggestion["action_target_label"] == "Ar potlasa"
    assert suggestion["action_target_params"] == {
        "business_unit_id": str(test_business_unit.id),
        "inventory_item_id": str(item.id),
        "quick_action": "complete_item_cost",
        "action_suggestion_id": suggestion["id"],
    }


def test_variance_action_suggestions_link_recipe_error_to_recipe_workflow(
    client: TestClient,
    db_session,
    create_inventory_item,
    create_inventory_movement,
    test_business_unit: BusinessUnitModel,
    test_unit_of_measure: UnitOfMeasureModel,
) -> None:
    item = create_inventory_item(
        business_unit_id=test_business_unit.id,
        uom_id=test_unit_of_measure.id,
        name="Recipe Error Flour",
        item_type="raw_material",
    )
    item.default_unit_cost = Decimal("3000.00")
    db_session.commit()

    movement = create_inventory_movement(
        business_unit_id=test_business_unit.id,
        inventory_item_id=item.id,
        movement_type="adjustment",
        quantity=Decimal("1.500"),
        uom_id=test_unit_of_measure.id,
        occurred_at=datetime.now(UTC) - timedelta(days=1),
    )
    movement.reason_code = "recipe_error"
    db_session.commit()

    response = client.get(
        f"{API_PREFIX}/variance-action-suggestions",
        params={"business_unit_id": str(test_business_unit.id), "days": 30},
    )

    assert response.status_code == 200
    suggestion = next(
        row for row in response.json() if row["action_type"] == "review_recipe_variance"
    )
    assert suggestion["action_target_type"] == "production_recipes"
    assert suggestion["action_target_label"] == "Receptek"
    assert suggestion["action_target_params"] == {
        "business_unit_id": str(test_business_unit.id),
        "reason_code": "recipe_error",
        "quick_action": "review_recipe_variance",
        "action_suggestion_id": suggestion["id"],
    }


def test_variance_action_suggestions_link_mapping_error_to_mapping_workflow(
    client: TestClient,
    db_session,
    create_inventory_item,
    create_inventory_movement,
    test_business_unit: BusinessUnitModel,
    test_unit_of_measure: UnitOfMeasureModel,
) -> None:
    item = create_inventory_item(
        business_unit_id=test_business_unit.id,
        uom_id=test_unit_of_measure.id,
        name="Mapping Error Flour",
        item_type="raw_material",
    )
    item.default_unit_cost = Decimal("2500.00")
    db_session.commit()

    movement = create_inventory_movement(
        business_unit_id=test_business_unit.id,
        inventory_item_id=item.id,
        movement_type="adjustment",
        quantity=Decimal("1.000"),
        uom_id=test_unit_of_measure.id,
        occurred_at=datetime.now(UTC) - timedelta(days=1),
    )
    movement.reason_code = "mapping_error"
    db_session.commit()

    response = client.get(
        f"{API_PREFIX}/variance-action-suggestions",
        params={"business_unit_id": str(test_business_unit.id), "days": 30},
    )

    assert response.status_code == 200
    suggestion = next(
        row
        for row in response.json()
        if row["action_type"] == "review_mapping_variance"
    )
    assert suggestion["action_target_type"] == "imports"
    assert suggestion["action_target_label"] == "Mapping review"
    assert suggestion["action_target_params"] == {
        "business_unit_id": str(test_business_unit.id),
        "reason_code": "mapping_error",
        "quick_action": "review_mapping_variance",
        "mapping_status": "pending",
        "action_suggestion_id": suggestion["id"],
    }


def test_variance_action_suggestions_link_missing_purchase_invoice_to_procurement_workflow(
    client: TestClient,
    db_session,
    create_inventory_item,
    create_inventory_movement,
    test_business_unit: BusinessUnitModel,
    test_unit_of_measure: UnitOfMeasureModel,
) -> None:
    item = create_inventory_item(
        business_unit_id=test_business_unit.id,
        uom_id=test_unit_of_measure.id,
        name="Missing Purchase Invoice Flour",
        item_type="raw_material",
    )
    item.default_unit_cost = Decimal("1800.00")
    db_session.commit()

    movement = create_inventory_movement(
        business_unit_id=test_business_unit.id,
        inventory_item_id=item.id,
        movement_type="adjustment",
        quantity=Decimal("4.000"),
        uom_id=test_unit_of_measure.id,
        occurred_at=datetime.now(UTC) - timedelta(days=1),
    )
    movement.reason_code = "missing_purchase_invoice"
    db_session.commit()

    response = client.get(
        f"{API_PREFIX}/variance-action-suggestions",
        params={"business_unit_id": str(test_business_unit.id), "days": 30},
    )

    assert response.status_code == 200
    suggestion = next(
        row
        for row in response.json()
        if row["action_type"] == "review_missing_purchase_invoice"
    )
    assert suggestion["action_target_type"] == "procurement_invoices"
    assert suggestion["action_target_label"] == "Szamlak"
    assert suggestion["action_target_params"] == {
        "business_unit_id": str(test_business_unit.id),
        "reason_code": "missing_purchase_invoice",
        "quick_action": "review_missing_purchase_invoice",
        "action_suggestion_id": suggestion["id"],
    }


@pytest.mark.parametrize(
    ("reason_code", "action_type", "target_label"),
    [
        ("waste", "review_waste_process", "Selejt kontroll"),
        ("breakage", "review_breakage_process", "Tores kontroll"),
        ("spoilage", "review_spoilage_process", "Romlas kontroll"),
        ("theft_suspected", "review_theft_suspected", "Celzott kontroll"),
    ],
)
def test_variance_action_suggestions_link_physical_reasons_to_stock_control_workflow(
    client: TestClient,
    db_session,
    create_inventory_item,
    create_inventory_movement,
    test_business_unit: BusinessUnitModel,
    test_unit_of_measure: UnitOfMeasureModel,
    reason_code: str,
    action_type: str,
    target_label: str,
) -> None:
    item = create_inventory_item(
        business_unit_id=test_business_unit.id,
        uom_id=test_unit_of_measure.id,
        name=f"Physical Control {reason_code}",
        item_type="raw_material",
    )
    item.default_unit_cost = Decimal("1200.00")
    db_session.commit()

    movement = create_inventory_movement(
        business_unit_id=test_business_unit.id,
        inventory_item_id=item.id,
        movement_type="adjustment",
        quantity=Decimal("1.000"),
        uom_id=test_unit_of_measure.id,
        occurred_at=datetime.now(UTC) - timedelta(days=1),
    )
    movement.reason_code = reason_code
    db_session.commit()

    response = client.get(
        f"{API_PREFIX}/variance-action-suggestions",
        params={"business_unit_id": str(test_business_unit.id), "days": 30},
    )

    assert response.status_code == 200
    suggestion = next(
        row for row in response.json() if row["action_type"] == action_type
    )
    assert suggestion["action_target_type"] == "inventory_theoretical_stock"
    assert suggestion["action_target_label"] == target_label
    assert suggestion["action_target_params"] == {
        "business_unit_id": str(test_business_unit.id),
        "reason_code": reason_code,
        "quick_action": action_type,
        "action_suggestion_id": suggestion["id"],
    }


def test_variance_action_suggestion_review_can_be_resolved_and_reopened(
    client: TestClient,
    db_session,
    create_inventory_item,
    create_inventory_movement,
    test_business_unit: BusinessUnitModel,
    test_unit_of_measure: UnitOfMeasureModel,
) -> None:
    item = create_inventory_item(
        business_unit_id=test_business_unit.id,
        uom_id=test_unit_of_measure.id,
        name="Action Review Flour",
        item_type="raw_material",
    )
    item.default_unit_cost = Decimal("5000.00")
    db_session.commit()
    movement = create_inventory_movement(
        business_unit_id=test_business_unit.id,
        inventory_item_id=item.id,
        movement_type="waste",
        quantity=Decimal("3.000"),
        uom_id=test_unit_of_measure.id,
        occurred_at=datetime.now(UTC) - timedelta(days=2),
    )
    movement.reason_code = "waste"
    db_session.commit()

    list_response = client.get(
        f"{API_PREFIX}/variance-action-suggestions",
        params={"business_unit_id": str(test_business_unit.id), "days": 30},
    )
    suggestion = next(
        row
        for row in list_response.json()
        if row["action_type"] == "investigate_high_loss_item"
    )

    resolved_response = client.put(
        f"{API_PREFIX}/variance-action-suggestions/{suggestion['id']}/review",
        json={
            "business_unit_id": str(test_business_unit.id),
            "status": "resolved",
            "note": "Checked with kitchen team.",
        },
    )

    assert resolved_response.status_code == 200
    resolved_payload = resolved_response.json()
    assert resolved_payload["suggestion_id"] == suggestion["id"]
    assert resolved_payload["status"] == "resolved"
    assert resolved_payload["note"] == "Checked with kitchen team."
    assert resolved_payload["resolved_at"] is not None

    reviewed_list_response = client.get(
        f"{API_PREFIX}/variance-action-suggestions",
        params={"business_unit_id": str(test_business_unit.id), "days": 30},
    )
    reviewed_suggestion = next(
        row for row in reviewed_list_response.json() if row["id"] == suggestion["id"]
    )
    assert reviewed_suggestion["review_status"] == "resolved"
    assert reviewed_suggestion["review_note"] == "Checked with kitchen team."
    assert reviewed_suggestion["reviewed_at"] is not None

    reopened_response = client.put(
        f"{API_PREFIX}/variance-action-suggestions/{suggestion['id']}/review",
        json={
            "business_unit_id": str(test_business_unit.id),
            "status": "open",
        },
    )

    assert reopened_response.status_code == 200
    reopened_payload = reopened_response.json()
    assert reopened_payload["status"] == "open"
    assert reopened_payload["resolved_at"] is None
