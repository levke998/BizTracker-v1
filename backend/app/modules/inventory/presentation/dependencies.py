"""Inventory presentation dependency wiring."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.modules.inventory.application.commands.create_inventory_movement import (
    CreateInventoryMovementCommand,
)
from app.modules.inventory.application.commands.register_physical_stock_count import (
    RegisterPhysicalStockCountCommand,
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
from app.modules.inventory.application.commands.upsert_variance_threshold import (
    UpsertInventoryVarianceThresholdCommand,
)
from app.modules.inventory.application.queries.list_inventory_items import (
    ListInventoryItemsQuery,
)
from app.modules.inventory.application.queries.get_variance_period_comparison import (
    GetInventoryVariancePeriodComparisonQuery,
)
from app.modules.inventory.application.queries.get_variance_threshold import (
    GetInventoryVarianceThresholdQuery,
)
from app.modules.inventory.application.queries.list_estimated_consumption import (
    ListEstimatedConsumptionAuditQuery,
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
from app.modules.inventory.application.queries.list_variance_reason_summary import (
    ListInventoryVarianceReasonSummaryQuery,
)
from app.modules.inventory.application.queries.list_variance_trend import (
    ListInventoryVarianceTrendQuery,
)
from app.modules.inventory.application.queries.list_variance_item_summary import (
    ListInventoryVarianceItemSummaryQuery,
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


def get_list_estimated_consumption_audit_query(
    session: DbSession,
) -> ListEstimatedConsumptionAuditQuery:
    """Wire the estimated consumption audit query to its repository."""

    repository = SqlAlchemyInventoryItemRepository(session)
    return ListEstimatedConsumptionAuditQuery(repository=repository)


def get_list_inventory_theoretical_stock_query(
    session: DbSession,
) -> ListInventoryTheoreticalStockQuery:
    """Wire the theoretical stock query to its repository."""

    repository = SqlAlchemyInventoryItemRepository(session)
    return ListInventoryTheoreticalStockQuery(repository=repository)


def get_list_inventory_variance_reason_summary_query(
    session: DbSession,
) -> ListInventoryVarianceReasonSummaryQuery:
    """Wire the variance reason summary query to its repository."""

    repository = SqlAlchemyInventoryItemRepository(session)
    return ListInventoryVarianceReasonSummaryQuery(repository=repository)


def get_list_inventory_variance_trend_query(
    session: DbSession,
) -> ListInventoryVarianceTrendQuery:
    """Wire the variance trend query to its repository."""

    repository = SqlAlchemyInventoryItemRepository(session)
    return ListInventoryVarianceTrendQuery(repository=repository)


def get_list_inventory_variance_item_summary_query(
    session: DbSession,
) -> ListInventoryVarianceItemSummaryQuery:
    """Wire the variance item summary query to its repository."""

    repository = SqlAlchemyInventoryItemRepository(session)
    return ListInventoryVarianceItemSummaryQuery(repository=repository)


def get_inventory_variance_period_comparison_query(
    session: DbSession,
) -> GetInventoryVariancePeriodComparisonQuery:
    """Wire the variance period comparison query to its repository."""

    repository = SqlAlchemyInventoryItemRepository(session)
    return GetInventoryVariancePeriodComparisonQuery(repository=repository)


def get_inventory_variance_threshold_query(
    session: DbSession,
) -> GetInventoryVarianceThresholdQuery:
    """Wire the variance threshold query to its repository."""

    repository = SqlAlchemyInventoryItemRepository(session)
    return GetInventoryVarianceThresholdQuery(repository=repository)


def get_upsert_inventory_variance_threshold_command(
    session: DbSession,
) -> UpsertInventoryVarianceThresholdCommand:
    """Wire the variance threshold upsert command to its repository."""

    repository = SqlAlchemyInventoryItemRepository(session)
    return UpsertInventoryVarianceThresholdCommand(repository=repository)


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


def get_register_physical_stock_count_command(
    session: DbSession,
) -> RegisterPhysicalStockCountCommand:
    """Wire the physical stock count command to its repository."""

    repository = SqlAlchemyInventoryItemRepository(session)
    return RegisterPhysicalStockCountCommand(repository=repository)
