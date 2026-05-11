"""Production presentation dependencies."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.modules.production.application.commands.create_recipe import (
    SaveActiveProductRecipeCommand,
)
from app.modules.production.application.queries.get_recipe_readiness_overview import (
    GetRecipeReadinessOverviewQuery,
)
from app.modules.production.application.queries.list_recipes import ListRecipesQuery
from app.modules.production.infrastructure.repositories.sqlalchemy_recipe_repository import (
    SqlAlchemyRecipeRepository,
)


def get_list_recipes_query(
    session: Annotated[Session, Depends(get_db_session)],
) -> ListRecipesQuery:
    """Provide the production recipe list query."""

    return ListRecipesQuery(repository=SqlAlchemyRecipeRepository(session))


def get_recipe_readiness_overview_query(
    session: Annotated[Session, Depends(get_db_session)],
) -> GetRecipeReadinessOverviewQuery:
    """Provide aggregate recipe readiness counters."""

    return GetRecipeReadinessOverviewQuery(
        repository=SqlAlchemyRecipeRepository(session),
    )


def get_save_recipe_command(
    session: Annotated[Session, Depends(get_db_session)],
) -> SaveActiveProductRecipeCommand:
    """Provide the production recipe save command."""

    return SaveActiveProductRecipeCommand(
        repository=SqlAlchemyRecipeRepository(session),
    )
