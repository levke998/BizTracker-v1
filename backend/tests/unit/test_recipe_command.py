"""Unit tests for production recipe write use cases."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from app.modules.production.application.commands.create_recipe import (
    RecipeValidationError,
    SaveActiveProductRecipeCommand,
)
from app.modules.production.domain.entities.recipe import (
    RecipeDraft,
    RecipeIngredientDraft,
)


class FakeRecipeRepository:
    def __init__(self) -> None:
        self.valid_unit_ids: set = set()
        self.valid_inventory_item_ids: set = set()
        self.saved_draft: RecipeDraft | None = None

    def list_recipe_summaries(self, **_kwargs):
        return []

    def unit_exists(self, uom_id):
        return uom_id in self.valid_unit_ids

    def inventory_item_belongs_to_business_unit(
        self,
        *,
        inventory_item_id,
        business_unit_id,
    ):
        return inventory_item_id in self.valid_inventory_item_ids

    def save_active_recipe(self, *, product_id, draft):
        self.saved_draft = draft


def test_save_active_recipe_command_validates_and_saves_draft() -> None:
    repository = FakeRecipeRepository()
    business_unit_id = uuid4()
    product_id = uuid4()
    uom_id = uuid4()
    inventory_item_id = uuid4()
    repository.valid_unit_ids.add(uom_id)
    repository.valid_inventory_item_ids.add(inventory_item_id)
    command = SaveActiveProductRecipeCommand(repository=repository)

    draft = RecipeDraft(
        name="Test recipe",
        yield_quantity=Decimal("10"),
        yield_uom_id=uom_id,
        ingredients=(
            RecipeIngredientDraft(
                inventory_item_id=inventory_item_id,
                quantity=Decimal("2"),
                uom_id=uom_id,
            ),
        ),
    )

    command.execute(
        product_id=product_id,
        business_unit_id=business_unit_id,
        draft=draft,
    )

    assert repository.saved_draft == draft


def test_save_active_recipe_command_rejects_duplicate_ingredients() -> None:
    repository = FakeRecipeRepository()
    business_unit_id = uuid4()
    product_id = uuid4()
    uom_id = uuid4()
    inventory_item_id = uuid4()
    repository.valid_unit_ids.add(uom_id)
    repository.valid_inventory_item_ids.add(inventory_item_id)
    command = SaveActiveProductRecipeCommand(repository=repository)

    draft = RecipeDraft(
        name="Duplicate recipe",
        yield_quantity=Decimal("1"),
        yield_uom_id=uom_id,
        ingredients=(
            RecipeIngredientDraft(
                inventory_item_id=inventory_item_id,
                quantity=Decimal("1"),
                uom_id=uom_id,
            ),
            RecipeIngredientDraft(
                inventory_item_id=inventory_item_id,
                quantity=Decimal("2"),
                uom_id=uom_id,
            ),
        ),
    )

    with pytest.raises(RecipeValidationError, match="same ingredient twice"):
        command.execute(
            product_id=product_id,
            business_unit_id=business_unit_id,
            draft=draft,
        )

    assert repository.saved_draft is None


def test_save_active_recipe_command_rejects_foreign_inventory_item() -> None:
    repository = FakeRecipeRepository()
    business_unit_id = uuid4()
    product_id = uuid4()
    uom_id = uuid4()
    repository.valid_unit_ids.add(uom_id)
    command = SaveActiveProductRecipeCommand(repository=repository)

    draft = RecipeDraft(
        name="Foreign item recipe",
        yield_quantity=Decimal("1"),
        yield_uom_id=uom_id,
        ingredients=(
            RecipeIngredientDraft(
                inventory_item_id=uuid4(),
                quantity=Decimal("1"),
                uom_id=uom_id,
            ),
        ),
    )

    with pytest.raises(RecipeValidationError, match="business unit"):
        command.execute(
            product_id=product_id,
            business_unit_id=business_unit_id,
            draft=draft,
        )

    assert repository.saved_draft is None
