"""Production recipe API."""

from __future__ import annotations

from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.modules.master_data.infrastructure.orm.product_model import ProductModel
from app.modules.production.application.commands.create_recipe import (
    RecipeValidationError,
    SaveActiveProductRecipeCommand,
)
from app.modules.production.application.queries.list_recipes import ListRecipesQuery
from app.modules.production.domain.entities.recipe import RecipeDraft, RecipeIngredientDraft
from app.modules.production.presentation.dependencies import (
    get_list_recipes_query,
    get_save_recipe_command,
)
from app.modules.production.presentation.schemas.recipe import (
    RecipeCostSummaryResponse,
    RecipeSaveRequest,
)

router = APIRouter(prefix="/production", tags=["production"])


@router.get("/recipes", response_model=list[RecipeCostSummaryResponse])
def list_recipes(
    business_unit_id: uuid.UUID,
    query: Annotated[ListRecipesQuery, Depends(get_list_recipes_query)],
    product_id: uuid.UUID | None = Query(default=None),
    active_only: bool = Query(default=True),
) -> list[RecipeCostSummaryResponse]:
    """Return recipe cost/readiness rows for product catalog items."""

    summaries = query.execute(
        business_unit_id=business_unit_id,
        product_id=product_id,
        active_only=active_only,
    )
    return [RecipeCostSummaryResponse.model_validate(summary) for summary in summaries]


@router.put(
    "/products/{product_id}/recipe",
    response_model=RecipeCostSummaryResponse,
)
def save_product_recipe(
    product_id: uuid.UUID,
    payload: RecipeSaveRequest,
    session: Annotated[Session, Depends(get_db_session)],
    command: Annotated[SaveActiveProductRecipeCommand, Depends(get_save_recipe_command)],
    query: Annotated[ListRecipesQuery, Depends(get_list_recipes_query)],
) -> RecipeCostSummaryResponse:
    """Save the product's next active recipe version."""

    product = session.get(ProductModel, product_id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )

    business_unit_id = product.business_unit_id
    try:
        command.execute(
            product_id=product.id,
            business_unit_id=business_unit_id,
            draft=_to_recipe_draft(payload),
        )
    except RecipeValidationError as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    session.commit()
    summaries = query.execute(
        business_unit_id=business_unit_id,
        product_id=product_id,
        active_only=False,
    )
    if not summaries:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product recipe summary not found.",
        )
    return RecipeCostSummaryResponse.model_validate(summaries[0])


def _to_recipe_draft(payload: RecipeSaveRequest) -> RecipeDraft:
    return RecipeDraft(
        name=payload.name,
        yield_quantity=payload.yield_quantity,
        yield_uom_id=payload.yield_uom_id,
        ingredients=tuple(
            RecipeIngredientDraft(
                inventory_item_id=ingredient.inventory_item_id,
                quantity=ingredient.quantity,
                uom_id=ingredient.uom_id,
            )
            for ingredient in payload.ingredients
        ),
    )
