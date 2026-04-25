"""Integration tests for catalog maintenance APIs."""

from __future__ import annotations

from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.modules.inventory.infrastructure.orm.inventory_item_model import (
    InventoryItemModel,
)
from app.modules.master_data.infrastructure.orm.category_model import CategoryModel
from app.modules.master_data.infrastructure.orm.product_model import ProductModel
from app.modules.master_data.infrastructure.orm.unit_of_measure_model import (
    UnitOfMeasureModel,
)
from app.modules.production.infrastructure.orm.recipe_model import (
    RecipeIngredientModel,
    RecipeModel,
    RecipeVersionModel,
)

API_PREFIX = "/api/v1/catalog"


def test_catalog_creates_product_with_recipe_and_updates_ingredient_stock(
    client: TestClient,
    db_session: Session,
    test_business_unit,
    pcs_unit_of_measure: UnitOfMeasureModel,
) -> None:
    category = CategoryModel(
        business_unit_id=test_business_unit.id,
        name="Catalog Test Category",
        is_active=True,
    )
    ingredient = InventoryItemModel(
        business_unit_id=test_business_unit.id,
        name="Catalog Test Flour",
        item_type="raw_material",
        uom_id=pcs_unit_of_measure.id,
        track_stock=True,
        default_unit_cost=Decimal("120"),
        estimated_stock_quantity=Decimal("50"),
        is_active=True,
    )
    db_session.add_all([category, ingredient])
    db_session.commit()

    created_product_id = None
    try:
        response = client.post(
            f"{API_PREFIX}/products",
            json={
                "business_unit_id": str(test_business_unit.id),
                "category_id": str(category.id),
                "sales_uom_id": str(pcs_unit_of_measure.id),
                "sku": "CAT-TEST-001",
                "name": "Catalog Test Cake",
                "product_type": "finished_good",
                "sale_price_gross": "990",
                "default_unit_cost": None,
                "currency": "HUF",
                "is_active": True,
                "recipe": {
                    "name": "Catalog Test Cake recipe",
                    "yield_quantity": "10",
                    "yield_uom_id": str(pcs_unit_of_measure.id),
                    "ingredients": [
                        {
                            "inventory_item_id": str(ingredient.id),
                            "quantity": "2",
                            "uom_id": str(pcs_unit_of_measure.id),
                        }
                    ],
                },
            },
        )

        assert response.status_code == 201
        payload = response.json()
        created_product_id = payload["id"]
        assert payload["has_recipe"] is True
        assert Decimal(payload["estimated_unit_cost"]) == Decimal("24")
        assert Decimal(payload["estimated_margin_amount"]) == Decimal("966")
        assert payload["ingredients"][0]["name"] == "Catalog Test Flour"

        ingredient_response = client.patch(
            f"{API_PREFIX}/ingredients/{ingredient.id}",
            json={
                "name": "Catalog Test Flour",
                "item_type": "raw_material",
                "uom_id": str(pcs_unit_of_measure.id),
                "track_stock": True,
                "default_unit_cost": "140",
                "estimated_stock_quantity": "75",
                "is_active": True,
            },
        )

        assert ingredient_response.status_code == 200
        ingredient_payload = ingredient_response.json()
        assert Decimal(ingredient_payload["default_unit_cost"]) == Decimal("140")
        assert Decimal(ingredient_payload["estimated_stock_quantity"]) == Decimal("75")

        delete_product_response = client.delete(
            f"{API_PREFIX}/products/{created_product_id}"
        )
        assert delete_product_response.status_code == 200
        assert delete_product_response.json()["is_active"] is False

        active_products_response = client.get(
            f"{API_PREFIX}/products",
            params={"business_unit_id": str(test_business_unit.id)},
        )
        assert active_products_response.status_code == 200
        assert created_product_id not in [
            item["id"] for item in active_products_response.json()
        ]

        inactive_products_response = client.get(
            f"{API_PREFIX}/products",
            params={
                "business_unit_id": str(test_business_unit.id),
                "active_only": False,
            },
        )
        assert inactive_products_response.status_code == 200
        assert created_product_id in [
            item["id"] for item in inactive_products_response.json()
        ]

        delete_ingredient_response = client.delete(
            f"{API_PREFIX}/ingredients/{ingredient.id}"
        )
        assert delete_ingredient_response.status_code == 200
        assert delete_ingredient_response.json()["is_active"] is False
    finally:
        db_session.rollback()
        if created_product_id is not None:
            recipe_ids = [
                recipe_id
                for recipe_id, in db_session.execute(
                    select(RecipeModel.id).where(RecipeModel.product_id == created_product_id)
                ).all()
            ]
            if recipe_ids:
                version_ids = [
                    version_id
                    for version_id, in db_session.execute(
                        select(RecipeVersionModel.id).where(
                            RecipeVersionModel.recipe_id.in_(recipe_ids)
                        )
                    ).all()
                ]
                if version_ids:
                    db_session.execute(
                        delete(RecipeIngredientModel).where(
                            RecipeIngredientModel.recipe_version_id.in_(version_ids)
                        )
                    )
                db_session.execute(
                    delete(RecipeVersionModel).where(
                        RecipeVersionModel.recipe_id.in_(recipe_ids)
                    )
                )
                db_session.execute(delete(RecipeModel).where(RecipeModel.id.in_(recipe_ids)))
            db_session.execute(delete(ProductModel).where(ProductModel.id == created_product_id))
        db_session.execute(delete(InventoryItemModel).where(InventoryItemModel.id == ingredient.id))
        db_session.execute(delete(CategoryModel).where(CategoryModel.id == category.id))
        db_session.commit()
