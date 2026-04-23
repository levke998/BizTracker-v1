"""Inventory presentation dependency wiring."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.modules.inventory.application.commands.create_inventory_item import (
    CreateInventoryItemCommand,
)
from app.modules.inventory.application.queries.list_inventory_items import (
    ListInventoryItemsQuery,
)
from app.modules.inventory.infrastructure.repositories.sqlalchemy_inventory_item_repository import (
    SqlAlchemyInventoryItemRepository,
)

DbSession = Annotated[Session, Depends(get_db_session)]


def get_list_inventory_items_query(session: DbSession) -> ListInventoryItemsQuery:
    """Wire the inventory item list query to its repository."""

    repository = SqlAlchemyInventoryItemRepository(session)
    return ListInventoryItemsQuery(repository=repository)


def get_create_inventory_item_command(session: DbSession) -> CreateInventoryItemCommand:
    """Wire the inventory create command to its repository."""

    repository = SqlAlchemyInventoryItemRepository(session)
    return CreateInventoryItemCommand(repository=repository)
