"""Integration tests for production recipe readiness APIs."""

from __future__ import annotations

from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.inventory.infrastructure.orm.inventory_item_model import (
    InventoryItemModel,
)
from app.modules.master_data.infrastructure.orm.product_model import ProductModel
from app.modules.master_data.infrastructure.orm.unit_of_measure_model import (
    UnitOfMeasureModel,
)
from app.modules.master_data.infrastructure.orm.vat_rate_model import VatRateModel
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
    vat_rate = db_session.scalar(select(VatRateModel).where(VatRateModel.code == "HU_27"))
    assert vat_rate is not None
    stockless_item = InventoryItemModel(
        business_unit_id=test_business_unit.id,
        name="Production Test Flour",
        item_type="raw_material",
        uom_id=pcs_unit_of_measure.id,
        default_vat_rate_id=vat_rate.id,
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
        default_vat_rate_id=vat_rate.id,
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
    assert stockless_row["tax_status"] == "product_vat_derived"
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

    overview_response = client.get(
        f"{API_PREFIX}/recipes/readiness-overview",
        params={"business_unit_id": str(test_business_unit.id)},
    )
    assert overview_response.status_code == 200
    overview = overview_response.json()
    assert overview["total_products"] == 3
    assert overview["ready_count"] == 0
    assert overview["incomplete_count"] == 3
    assert overview["critical_count"] == 2
    assert overview["readiness_counts"]["missing_recipe"] == 1
    assert overview["readiness_counts"]["missing_cost"] == 1
    assert overview["readiness_counts"]["missing_stock"] == 1
    assert overview["next_actions"] == [
        "create_missing_recipes",
        "fill_missing_ingredient_costs",
        "review_stock_shortages",
    ]


def test_production_recipe_endpoint_saves_next_active_recipe_version(
    client: TestClient,
    db_session: Session,
    test_business_unit,
    pcs_unit_of_measure: UnitOfMeasureModel,
) -> None:
    vat_rate = db_session.scalar(select(VatRateModel).where(VatRateModel.code == "HU_27"))
    assert vat_rate is not None
    ingredient = InventoryItemModel(
        business_unit_id=test_business_unit.id,
        name="Production Endpoint Flour",
        item_type="raw_material",
        uom_id=pcs_unit_of_measure.id,
        default_vat_rate_id=vat_rate.id,
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


def test_production_recipe_costing_keeps_mixed_vat_rates_separate(
    client: TestClient,
    db_session: Session,
    test_business_unit,
    pcs_unit_of_measure: UnitOfMeasureModel,
) -> None:
    rates = {
        rate.code: rate
        for rate in db_session.scalars(
            select(VatRateModel).where(VatRateModel.code.in_(("HU_5", "HU_18", "HU_27")))
        ).all()
    }
    assert {"HU_5", "HU_18", "HU_27"} <= set(rates)

    items = [
        InventoryItemModel(
            business_unit_id=test_business_unit.id,
            name="Production VAT Milk",
            item_type="raw_material",
            uom_id=pcs_unit_of_measure.id,
            default_vat_rate_id=rates["HU_5"].id,
            track_stock=True,
            default_unit_cost=Decimal("100"),
            estimated_stock_quantity=Decimal("10"),
            is_active=True,
        ),
        InventoryItemModel(
            business_unit_id=test_business_unit.id,
            name="Production VAT Pastry",
            item_type="raw_material",
            uom_id=pcs_unit_of_measure.id,
            default_vat_rate_id=rates["HU_18"].id,
            track_stock=True,
            default_unit_cost=Decimal("200"),
            estimated_stock_quantity=Decimal("10"),
            is_active=True,
        ),
        InventoryItemModel(
            business_unit_id=test_business_unit.id,
            name="Production VAT Soda",
            item_type="resale_good",
            uom_id=pcs_unit_of_measure.id,
            default_vat_rate_id=rates["HU_27"].id,
            track_stock=True,
            default_unit_cost=Decimal("300"),
            estimated_stock_quantity=Decimal("10"),
            is_active=True,
        ),
    ]
    product = ProductModel(
        business_unit_id=test_business_unit.id,
        name="Production Mixed VAT Basket",
        product_type="finished_good",
        sales_uom_id=pcs_unit_of_measure.id,
        sale_price_gross=Decimal("1200"),
        currency="HUF",
        is_active=True,
    )
    db_session.add_all([*items, product])
    db_session.flush()

    recipe_version = _add_recipe(
        db_session,
        product_id=product.id,
        product_name=product.name,
        yield_uom_id=pcs_unit_of_measure.id,
    )
    db_session.add_all(
        [
            RecipeIngredientModel(
                recipe_version_id=recipe_version.id,
                inventory_item_id=item.id,
                quantity=Decimal("1"),
                uom_id=pcs_unit_of_measure.id,
            )
            for item in items
        ]
    )
    db_session.commit()

    response = client.get(
        f"{API_PREFIX}/recipes",
        params={"business_unit_id": str(test_business_unit.id)},
    )

    assert response.status_code == 200
    row = next(
        item for item in response.json() if item["product_name"] == product.name
    )
    assert row["cost_status"] == "complete"
    assert row["tax_status"] == "product_vat_derived"
    assert row["warnings"] == []
    assert Decimal(row["total_cost"]) == Decimal("600")
    assert Decimal(row["total_vat_amount"]) == Decimal("122.00")
    assert Decimal(row["total_gross_cost"]) == Decimal("722.00")
    assert Decimal(row["unit_gross_cost"]) == Decimal("72.20")
    ingredient_rates = {
        ingredient["inventory_item_name"]: Decimal(str(ingredient["vat_rate_percent"]))
        for ingredient in row["ingredients"]
    }
    assert ingredient_rates == {
        "Production VAT Milk": Decimal("5.0000"),
        "Production VAT Pastry": Decimal("18.0000"),
        "Production VAT Soda": Decimal("27.0000"),
    }


def test_production_recipe_costing_flags_missing_vat_without_blocking_net_cost(
    client: TestClient,
    db_session: Session,
    test_business_unit,
    pcs_unit_of_measure: UnitOfMeasureModel,
) -> None:
    ingredient = InventoryItemModel(
        business_unit_id=test_business_unit.id,
        name="Production Missing VAT Ingredient",
        item_type="raw_material",
        uom_id=pcs_unit_of_measure.id,
        track_stock=True,
        default_unit_cost=Decimal("100"),
        estimated_stock_quantity=Decimal("10"),
        is_active=True,
    )
    product = ProductModel(
        business_unit_id=test_business_unit.id,
        name="Production Missing VAT Product",
        product_type="finished_good",
        sales_uom_id=pcs_unit_of_measure.id,
        sale_price_gross=Decimal("500"),
        currency="HUF",
        is_active=True,
    )
    db_session.add_all([ingredient, product])
    db_session.flush()
    recipe_version = _add_recipe(
        db_session,
        product_id=product.id,
        product_name=product.name,
        yield_uom_id=pcs_unit_of_measure.id,
    )
    db_session.add(
        RecipeIngredientModel(
            recipe_version_id=recipe_version.id,
            inventory_item_id=ingredient.id,
            quantity=Decimal("1"),
            uom_id=pcs_unit_of_measure.id,
        )
    )
    db_session.commit()

    response = client.get(
        f"{API_PREFIX}/recipes",
        params={"business_unit_id": str(test_business_unit.id)},
    )

    assert response.status_code == 200
    row = next(
        item for item in response.json() if item["product_name"] == product.name
    )
    assert row["cost_status"] == "complete"
    assert row["readiness_status"] == "ready"
    assert row["tax_status"] == "missing_vat_rate"
    assert row["warnings"] == ["missing_vat_rate"]
    assert Decimal(row["unit_cost"]) == Decimal("10")
    assert row["total_vat_amount"] is None
    assert row["total_gross_cost"] is None


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
