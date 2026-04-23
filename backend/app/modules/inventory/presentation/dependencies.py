"""Inventory presentation dependency wiring."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.modules.inventory.application.commands.create_inventory_movement import (
    CreateInventoryMovementCommand,
)
from app.modules.inventory.application.commands.archive_inventory_item import (
    ArchiveInventoryItemCommand,
)
from app.modules.inventory.application.commands.create_inventory_item import (
    CreateInventoryItemCommand,
)
from app.modules.inventory.application.commands.update_inventory_item import (
    UpdateInventoryItemCommand,
)
from app.modules.inventory.application.queries.list_inventory_items import (
    ListInventoryItemsQuery,
)
from app.modules.inventory.application.queries.list_inventory_movements import (
    ListInventoryMovementsQuery,
)
from app.modules.inventory.application.queries.list_stock_levels import (
    ListInventoryStockLevelsQuery,
)
from app.modules.inventory.application.queries.list_theoretical_stock import (
    ListInventoryTheoreticalStockQuery,
)
from app.modules.inventory.infrastructure.repositories.sqlalchemy_inventory_item_repository import (
    SqlAlchemyInventoryItemRepository,
)

DbSession = Annotated[Session, Depends(get_db_session)]


def get_list_inventory_items_query(session: DbSession) -> ListInventoryItemsQuery:
    """Wire the inventory item list query to its repository."""

    repository = SqlAlchemyInventoryItemRepository(session)
    return ListInventoryItemsQuery(repository=repository)


def get_list_inventory_movements_query(
    session: DbSession,
) -> ListInventoryMovementsQuery:
    """Wire the movement list query to its repository."""

    repository = SqlAlchemyInventoryItemRepository(session)
    return ListInventoryMovementsQuery(repository=repository)


def get_list_inventory_stock_levels_query(
    session: DbSession,
) -> ListInventoryStockLevelsQuery:
    """Wire the stock level query to its repository."""

    repository = SqlAlchemyInventoryItemRepository(session)
    return ListInventoryStockLevelsQuery(repository=repository)


def get_list_inventory_theoretical_stock_query(
    session: DbSession,
) -> ListInventoryTheoreticalStockQuery:
    """Wire the theoretical stock query to its repository."""

    repository = SqlAlchemyInventoryItemRepository(session)
    return ListInventoryTheoreticalStockQuery(repository=repository)


def get_create_inventory_item_command(session: DbSession) -> CreateInventoryItemCommand:
    """Wire the inventory create command to its repository."""

    repository = SqlAlchemyInventoryItemRepository(session)
    return CreateInventoryItemCommand(repository=repository)


def get_update_inventory_item_command(session: DbSession) -> UpdateInventoryItemCommand:
    """Wire the inventory update command to its repository."""

    repository = SqlAlchemyInventoryItemRepository(session)
    return UpdateInventoryItemCommand(repository=repository)


def get_archive_inventory_item_command(session: DbSession) -> ArchiveInventoryItemCommand:
    """Wire the inventory archive command to its repository."""

    repository = SqlAlchemyInventoryItemRepository(session)
    return ArchiveInventoryItemCommand(repository=repository)


def get_create_inventory_movement_command(
    session: DbSession,
) -> CreateInventoryMovementCommand:
    """Wire the inventory movement command to its repository."""

    repository = SqlAlchemyInventoryItemRepository(session)
    return CreateInventoryMovementCommand(repository=repository)
