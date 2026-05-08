"""Integration tests for production recipe readiness APIs."""

from __future__ import annotations

from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.modules.inventory.infrastructure.orm.inventory_item_model import (
    InventoryItemModel,
)
from app.modules.master_data.infrastructure.orm.product_model import ProductModel
from app.modules.master_data.infrastructure.orm.unit_of_measure_model import (
    UnitOfMeasureModel,
)
from app.modules.production.infrastructure.orm.recipe_model import (
    RecipeIngredientModel,
    RecipeModel,
    RecipeVersionModel,
)

API_PREFIX = "/api/v1/production"


def test_production_recipes_report_readiness_without_blocking_zero_stock(
    client: TestClient,
    db_session: Session,
    test_business_unit,
    pcs_unit_of_measure: UnitOfMeasureModel,
) -> None:
    stockless_item = InventoryItemModel(
        business_unit_id=test_business_unit.id,
        name="Production Test Flour",
        item_type="raw_material",
        uom_id=pcs_unit_of_measure.id,
        track_stock=True,
        default_unit_cost=Decimal("120"),
        estimated_stock_quantity=Decimal("0"),
        is_active=True,
    )
    missing_cost_item = InventoryItemModel(
        business_unit_id=test_business_unit.id,
        name="Production Test Sugar",
        item_type="raw_material",
        uom_id=pcs_unit_of_measure.id,
        track_stock=True,
        default_unit_cost=None,
        estimated_stock_quantity=Decimal("10"),
        is_active=True,
    )
    stockless_product = ProductModel(
        business_unit_id=test_business_unit.id,
        name="Production Test Cake",
        product_type="finished_good",
        sales_uom_id=pcs_unit_of_measure.id,
        sale_price_gross=Decimal("990"),
        currency="HUF",
        is_active=True,
    )
    missing_cost_product = ProductModel(
        business_unit_id=test_business_unit.id,
        name="Production Test Syrup",
        product_type="finished_good",
        sales_uom_id=pcs_unit_of_measure.id,
        sale_price_gross=Decimal("650"),
        currency="HUF",
        is_active=True,
    )
    no_recipe_product = ProductModel(
        business_unit_id=test_business_unit.id,
        name="Production Test Lemonade",
        product_type="finished_good",
        sales_uom_id=pcs_unit_of_measure.id,
        sale_price_gross=Decimal("750"),
        currency="HUF",
        is_active=True,
    )
    db_session.add_all(
        [
            stockless_item,
            missing_cost_item,
            stockless_product,
            missing_cost_product,
            no_recipe_product,
        ]
    )
    db_session.flush()

    stockless_recipe = _add_recipe(
        db_session,
        product_id=stockless_product.id,
        product_name=stockless_product.name,
        yield_uom_id=pcs_unit_of_measure.id,
    )
    missing_cost_recipe = _add_recipe(
        db_session,
        product_id=missing_cost_product.id,
        product_name=missing_cost_product.name,
        yield_uom_id=pcs_unit_of_measure.id,
    )
    db_session.add_all(
        [
            RecipeIngredientModel(
                recipe_version_id=stockless_recipe.id,
                inventory_item_id=stockless_item.id,
                quantity=Decimal("2"),
                uom_id=pcs_unit_of_measure.id,
            ),
            RecipeIngredientModel(
                recipe_version_id=missing_cost_recipe.id,
                inventory_item_id=missing_cost_item.id,
                quantity=Decimal("1"),
                uom_id=pcs_unit_of_measure.id,
            ),
        ]
    )
    db_session.commit()

    response = client.get(
        f"{API_PREFIX}/recipes",
        params={"business_unit_id": str(test_business_unit.id)},
    )

    assert response.status_code == 200
    rows = {row["product_name"]: row for row in response.json()}

    stockless_row = rows["Production Test Cake"]
    assert stockless_row["cost_status"] == "complete"
    assert stockless_row["readiness_status"] == "missing_stock"
    assert stockless_row["warnings"] == ["missing_stock"]
    assert Decimal(stockless_row["unit_cost"]) == Decimal("24")
    assert stockless_row["ingredients"][0]["stock_status"] == "missing"

    missing_cost_row = rows["Production Test Syrup"]
    assert missing_cost_row["cost_status"] == "missing_cost"
    assert missing_cost_row["readiness_status"] == "missing_cost"
    assert missing_cost_row["unit_cost"] is None
    assert missing_cost_row["known_total_cost"] == "0"

    no_recipe_row = rows["Production Test Lemonade"]
    assert no_recipe_row["cost_status"] == "no_recipe"
    assert no_recipe_row["readiness_status"] == "missing_recipe"
    assert no_recipe_row["ingredients"] == []


def test_production_recipe_endpoint_saves_next_active_recipe_version(
    client: TestClient,
    db_session: Session,
    test_business_unit,
    pcs_unit_of_measure: UnitOfMeasureModel,
) -> None:
    ingredient = InventoryItemModel(
        business_unit_id=test_business_unit.id,
        name="Production Endpoint Flour",
        item_type="raw_material",
        uom_id=pcs_unit_of_measure.id,
        track_stock=True,
        default_unit_cost=Decimal("200"),
        estimated_stock_quantity=Decimal("10"),
        is_active=True,
    )
    product = ProductModel(
        business_unit_id=test_business_unit.id,
        name="Production Endpoint Cake",
        product_type="finished_good",
        sales_uom_id=pcs_unit_of_measure.id,
        sale_price_gross=Decimal("1200"),
        currency="HUF",
        is_active=True,
    )
    db_session.add_all([ingredient, product])
    db_session.commit()

    response = client.put(
        f"{API_PREFIX}/products/{product.id}/recipe",
        json={
            "name": "Production Endpoint Cake recipe",
            "yield_quantity": "4",
            "yield_uom_id": str(pcs_unit_of_measure.id),
            "ingredients": [
                {
                    "inventory_item_id": str(ingredient.id),
                    "quantity": "2",
                    "uom_id": str(pcs_unit_of_measure.id),
                }
            ],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["product_id"] == str(product.id)
    assert payload["recipe_name"] == "Production Endpoint Cake recipe"
    assert payload["version_no"] == 1
    assert payload["cost_status"] == "complete"
    assert Decimal(payload["unit_cost"]) == Decimal("100")

    second_response = client.put(
        f"{API_PREFIX}/products/{product.id}/recipe",
        json={
            "name": "Production Endpoint Cake recipe v2",
            "yield_quantity": "2",
            "yield_uom_id": str(pcs_unit_of_measure.id),
            "ingredients": [
                {
                    "inventory_item_id": str(ingredient.id),
                    "quantity": "1",
                    "uom_id": str(pcs_unit_of_measure.id),
                }
            ],
        },
    )

    assert second_response.status_code == 200
    second_payload = second_response.json()
    assert second_payload["recipe_name"] == "Production Endpoint Cake recipe v2"
    assert second_payload["version_no"] == 2
    assert Decimal(second_payload["unit_cost"]) == Decimal("100")


def _add_recipe(
    db_session: Session,
    *,
    product_id,
    product_name: str,
    yield_uom_id,
) -> RecipeVersionModel:
    recipe = RecipeModel(
        product_id=product_id,
        name=f"{product_name} recipe",
        is_active=True,
    )
    db_session.add(recipe)
    db_session.flush()
    version = RecipeVersionModel(
        recipe_id=recipe.id,
        version_no=1,
        is_active=True,
        yield_quantity=Decimal("10"),
        yield_uom_id=yield_uom_id,
        notes="Production readiness test",
    )
    db_session.add(version)
    db_session.flush()
    return version
