"""Inventory SQLAlchemy repository."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.inventory.domain.entities.inventory_item import (
    EstimatedConsumptionAudit,
    InventoryItem,
    InventoryMovement,
    InventoryStockLevel,
    InventoryVarianceItemSummary,
    InventoryVariancePeriodComparison,
    InventoryVarianceReasonSummary,
    InventoryVarianceThreshold,
    InventoryVarianceTrendPoint,
    NewInventoryItem,
    NewInventoryMovement,
)
from app.modules.inventory.infrastructure.orm.estimated_consumption_model import (
    EstimatedConsumptionAuditModel,
)
from app.modules.inventory.infrastructure.orm.inventory_movement_model import (
    InventoryMovementModel,
)
from app.modules.inventory.infrastructure.orm.inventory_variance_threshold_model import (
    InventoryVarianceThresholdModel,
)
from app.modules.inventory.infrastructure.orm.inventory_item_model import (
    InventoryItemModel,
)
from app.modules.master_data.infrastructure.orm.business_unit_model import (
    BusinessUnitModel,
)
from app.modules.master_data.infrastructure.orm.product_model import ProductModel
from app.modules.master_data.infrastructure.orm.unit_of_measure_model import (
    UnitOfMeasureModel,
)


class SqlAlchemyInventoryItemRepository:
    """Read-side SQLAlchemy repository for inventory items."""

    HIGH_LOSS_VALUE_THRESHOLD = Decimal("10000")
    WORSENING_PERCENT_THRESHOLD = Decimal("25")
    MONEY_QUANT = Decimal("0.01")
    PERCENT_QUANT = Decimal("0.01")

    def __init__(self, session: Session) -> None:
        self._session = session

    def list_many(
        self,
        *,
        business_unit_id: uuid.UUID | None = None,
        item_type: str | None = None,
        limit: int = 50,
    ) -> list[InventoryItem]:
        statement = select(InventoryItemModel)

        if business_unit_id is not None:
            statement = statement.where(
                InventoryItemModel.business_unit_id == business_unit_id
            )
        if item_type is not None:
            statement = statement.where(InventoryItemModel.item_type == item_type)

        statement = statement.order_by(InventoryItemModel.name.asc()).limit(limit)
        models = self._session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def create(self, item: NewInventoryItem) -> InventoryItem:
        model = InventoryItemModel(
            business_unit_id=item.business_unit_id,
            name=item.name,
            item_type=item.item_type,
            uom_id=item.uom_id,
            track_stock=item.track_stock,
            is_active=item.is_active,
        )
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return self._to_entity(model)

    def update(
        self,
        *,
        inventory_item_id: uuid.UUID,
        name: str,
        item_type: str,
        uom_id: uuid.UUID,
        track_stock: bool,
        is_active: bool,
    ) -> InventoryItem:
        model = self._session.get(InventoryItemModel, inventory_item_id)
        if model is None:
            raise ValueError(f"Inventory item {inventory_item_id} was not found.")

        model.name = name
        model.item_type = item_type
        model.uom_id = uom_id
        model.track_stock = track_stock
        model.is_active = is_active

        self._session.commit()
        self._session.refresh(model)
        return self._to_entity(model)

    def archive(self, inventory_item_id: uuid.UUID) -> InventoryItem:
        model = self._session.get(InventoryItemModel, inventory_item_id)
        if model is None:
            raise ValueError(f"Inventory item {inventory_item_id} was not found.")

        model.is_active = False

        self._session.commit()
        self._session.refresh(model)
        return self._to_entity(model)

    def create_movement(self, movement: NewInventoryMovement) -> InventoryMovement:
        model = InventoryMovementModel(
            business_unit_id=movement.business_unit_id,
            inventory_item_id=movement.inventory_item_id,
            movement_type=movement.movement_type,
            quantity=movement.quantity,
            uom_id=movement.uom_id,
            unit_cost=movement.unit_cost,
            reason_code=movement.reason_code,
            note=movement.note,
            source_type=movement.source_type,
            source_id=movement.source_id,
            occurred_at=movement.occurred_at,
        )
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return self._to_movement_entity(model)

    def list_movements(
        self,
        *,
        business_unit_id: uuid.UUID | None = None,
        inventory_item_id: uuid.UUID | None = None,
        movement_type: str | None = None,
        limit: int = 50,
    ) -> list[InventoryMovement]:
        statement = select(InventoryMovementModel)

        if business_unit_id is not None:
            statement = statement.where(
                InventoryMovementModel.business_unit_id == business_unit_id
            )
        if inventory_item_id is not None:
            statement = statement.where(
                InventoryMovementModel.inventory_item_id == inventory_item_id
            )
        if movement_type is not None:
            statement = statement.where(
                InventoryMovementModel.movement_type == movement_type
            )

        statement = statement.order_by(
            InventoryMovementModel.occurred_at.desc(),
            InventoryMovementModel.created_at.desc(),
        ).limit(limit)

        models = self._session.scalars(statement).all()
        return [self._to_movement_entity(model) for model in models]

    def list_variance_reason_summary(
        self,
        *,
        business_unit_id: uuid.UUID | None = None,
        inventory_item_id: uuid.UUID | None = None,
        limit: int = 20,
    ) -> list[InventoryVarianceReasonSummary]:
        signed_quantity = sa.case(
            (
                InventoryMovementModel.movement_type == "adjustment",
                InventoryMovementModel.quantity,
            ),
            (
                InventoryMovementModel.movement_type == "waste",
                -InventoryMovementModel.quantity,
            ),
            else_=0,
        )

        statement = (
            select(
                InventoryMovementModel.reason_code,
                func.count(InventoryMovementModel.id).label("movement_count"),
                func.coalesce(func.sum(InventoryMovementModel.quantity), 0).label(
                    "total_quantity"
                ),
                func.coalesce(func.sum(signed_quantity), 0).label("net_quantity_delta"),
                func.max(InventoryMovementModel.occurred_at).label("latest_occurred_at"),
            )
            .where(InventoryMovementModel.reason_code.is_not(None))
            .where(InventoryMovementModel.movement_type.in_(["adjustment", "waste"]))
            .group_by(InventoryMovementModel.reason_code)
        )

        if business_unit_id is not None:
            statement = statement.where(
                InventoryMovementModel.business_unit_id == business_unit_id
            )
        if inventory_item_id is not None:
            statement = statement.where(
                InventoryMovementModel.inventory_item_id == inventory_item_id
            )

        rows = self._session.execute(
            statement.order_by(
                sa.desc("movement_count"),
                sa.desc("latest_occurred_at"),
            ).limit(limit)
        ).all()
        return [
            InventoryVarianceReasonSummary(
                reason_code=row.reason_code,
                movement_count=row.movement_count,
                total_quantity=Decimal(row.total_quantity),
                net_quantity_delta=Decimal(row.net_quantity_delta),
                latest_occurred_at=row.latest_occurred_at,
            )
            for row in rows
        ]

    def list_variance_trend(
        self,
        *,
        business_unit_id: uuid.UUID | None = None,
        inventory_item_id: uuid.UUID | None = None,
        days: int = 30,
    ) -> list[InventoryVarianceTrendPoint]:
        since = datetime.now(UTC) - timedelta(days=days)
        shortage_quantity = sa.case(
            (
                InventoryMovementModel.movement_type == "waste",
                InventoryMovementModel.quantity,
            ),
            else_=0,
        )
        surplus_quantity = sa.case(
            (
                InventoryMovementModel.movement_type == "adjustment",
                InventoryMovementModel.quantity,
            ),
            else_=0,
        )
        signed_quantity = sa.case(
            (
                InventoryMovementModel.movement_type == "adjustment",
                InventoryMovementModel.quantity,
            ),
            (
                InventoryMovementModel.movement_type == "waste",
                -InventoryMovementModel.quantity,
            ),
            else_=0,
        )
        unit_cost = func.coalesce(InventoryItemModel.default_unit_cost, 0)
        shortage_value = sa.case(
            (
                InventoryMovementModel.movement_type == "waste",
                InventoryMovementModel.quantity * unit_cost,
            ),
            else_=0,
        )
        surplus_value = sa.case(
            (
                InventoryMovementModel.movement_type == "adjustment",
                InventoryMovementModel.quantity * unit_cost,
            ),
            else_=0,
        )
        signed_value = sa.case(
            (
                InventoryMovementModel.movement_type == "adjustment",
                InventoryMovementModel.quantity * unit_cost,
            ),
            (
                InventoryMovementModel.movement_type == "waste",
                -(InventoryMovementModel.quantity * unit_cost),
            ),
            else_=0,
        )
        missing_cost_movement = sa.case(
            (
                InventoryItemModel.default_unit_cost.is_(None),
                1,
            ),
            else_=0,
        )
        bucket_date = func.date(InventoryMovementModel.occurred_at)

        statement = (
            select(
                bucket_date.label("bucket_date"),
                func.count(InventoryMovementModel.id).label("movement_count"),
                func.coalesce(func.sum(shortage_quantity), 0).label("shortage_quantity"),
                func.coalesce(func.sum(surplus_quantity), 0).label("surplus_quantity"),
                func.coalesce(func.sum(signed_quantity), 0).label("net_quantity_delta"),
                func.coalesce(func.sum(shortage_value), 0).label(
                    "estimated_shortage_value"
                ),
                func.coalesce(func.sum(surplus_value), 0).label(
                    "estimated_surplus_value"
                ),
                func.coalesce(func.sum(signed_value), 0).label(
                    "estimated_net_value_delta"
                ),
                func.coalesce(func.sum(missing_cost_movement), 0).label(
                    "missing_cost_movement_count"
                ),
            )
            .select_from(InventoryMovementModel)
            .join(
                InventoryItemModel,
                InventoryItemModel.id == InventoryMovementModel.inventory_item_id,
            )
            .where(InventoryMovementModel.reason_code.is_not(None))
            .where(InventoryMovementModel.movement_type.in_(["adjustment", "waste"]))
            .where(InventoryMovementModel.occurred_at >= since)
            .group_by(bucket_date)
        )

        if business_unit_id is not None:
            statement = statement.where(
                InventoryMovementModel.business_unit_id == business_unit_id
            )
        if inventory_item_id is not None:
            statement = statement.where(
                InventoryMovementModel.inventory_item_id == inventory_item_id
            )

        rows = self._session.execute(statement.order_by(bucket_date.asc())).all()
        return [
            InventoryVarianceTrendPoint(
                bucket_date=datetime.combine(row.bucket_date, datetime.min.time(), tzinfo=UTC),
                movement_count=row.movement_count,
                shortage_quantity=Decimal(row.shortage_quantity),
                surplus_quantity=Decimal(row.surplus_quantity),
                net_quantity_delta=Decimal(row.net_quantity_delta),
                estimated_shortage_value=self._money(row.estimated_shortage_value),
                estimated_surplus_value=self._money(row.estimated_surplus_value),
                estimated_net_value_delta=self._money(row.estimated_net_value_delta),
                missing_cost_movement_count=row.missing_cost_movement_count,
            )
            for row in rows
        ]

    def list_variance_item_summary(
        self,
        *,
        business_unit_id: uuid.UUID | None = None,
        limit: int = 20,
    ) -> list[InventoryVarianceItemSummary]:
        shortage_quantity = sa.case(
            (
                InventoryMovementModel.movement_type == "waste",
                InventoryMovementModel.quantity,
            ),
            else_=0,
        )
        surplus_quantity = sa.case(
            (
                InventoryMovementModel.movement_type == "adjustment",
                InventoryMovementModel.quantity,
            ),
            else_=0,
        )
        signed_quantity = sa.case(
            (
                InventoryMovementModel.movement_type == "adjustment",
                InventoryMovementModel.quantity,
            ),
            (
                InventoryMovementModel.movement_type == "waste",
                -InventoryMovementModel.quantity,
            ),
            else_=0,
        )
        unit_cost = func.coalesce(InventoryItemModel.default_unit_cost, 0)
        shortage_value = sa.case(
            (
                InventoryMovementModel.movement_type == "waste",
                InventoryMovementModel.quantity * unit_cost,
            ),
            else_=0,
        )
        surplus_value = sa.case(
            (
                InventoryMovementModel.movement_type == "adjustment",
                InventoryMovementModel.quantity * unit_cost,
            ),
            else_=0,
        )
        signed_value = sa.case(
            (
                InventoryMovementModel.movement_type == "adjustment",
                InventoryMovementModel.quantity * unit_cost,
            ),
            (
                InventoryMovementModel.movement_type == "waste",
                -(InventoryMovementModel.quantity * unit_cost),
            ),
            else_=0,
        )
        missing_cost_movement = sa.case(
            (
                InventoryItemModel.default_unit_cost.is_(None),
                1,
            ),
            else_=0,
        )

        statement = (
            select(
                InventoryItemModel.id.label("inventory_item_id"),
                InventoryItemModel.name,
                InventoryItemModel.item_type,
                InventoryItemModel.default_unit_cost,
                func.count(InventoryMovementModel.id).label("movement_count"),
                func.coalesce(func.sum(shortage_quantity), 0).label("shortage_quantity"),
                func.coalesce(func.sum(surplus_quantity), 0).label("surplus_quantity"),
                func.coalesce(func.sum(signed_quantity), 0).label("net_quantity_delta"),
                func.coalesce(func.sum(shortage_value), 0).label(
                    "estimated_shortage_value"
                ),
                func.coalesce(func.sum(surplus_value), 0).label(
                    "estimated_surplus_value"
                ),
                func.coalesce(func.sum(signed_value), 0).label(
                    "estimated_net_value_delta"
                ),
                func.coalesce(func.sum(missing_cost_movement), 0).label(
                    "missing_cost_movement_count"
                ),
                func.max(InventoryMovementModel.occurred_at).label("latest_occurred_at"),
            )
            .select_from(InventoryMovementModel)
            .join(
                InventoryItemModel,
                InventoryItemModel.id == InventoryMovementModel.inventory_item_id,
            )
            .where(InventoryMovementModel.reason_code.is_not(None))
            .where(InventoryMovementModel.movement_type.in_(["adjustment", "waste"]))
            .group_by(
                InventoryItemModel.id,
                InventoryItemModel.name,
                InventoryItemModel.item_type,
                InventoryItemModel.default_unit_cost,
            )
        )

        if business_unit_id is not None:
            statement = statement.where(
                InventoryMovementModel.business_unit_id == business_unit_id
            )

        rows = self._session.execute(
            statement.order_by(
                sa.desc("shortage_quantity"),
                sa.desc("movement_count"),
                sa.desc("latest_occurred_at"),
            ).limit(limit)
        ).all()
        return [
            InventoryVarianceItemSummary(
                inventory_item_id=row.inventory_item_id,
                name=row.name,
                item_type=row.item_type,
                default_unit_cost=(
                    self._money(row.default_unit_cost)
                    if row.default_unit_cost is not None
                    else None
                ),
                movement_count=row.movement_count,
                shortage_quantity=Decimal(row.shortage_quantity),
                surplus_quantity=Decimal(row.surplus_quantity),
                net_quantity_delta=Decimal(row.net_quantity_delta),
                estimated_shortage_value=self._money(row.estimated_shortage_value)
                if row.missing_cost_movement_count == 0
                else None,
                estimated_surplus_value=self._money(row.estimated_surplus_value)
                if row.missing_cost_movement_count == 0
                else None,
                estimated_net_value_delta=self._money(row.estimated_net_value_delta)
                if row.missing_cost_movement_count == 0
                else None,
                missing_cost_movement_count=row.missing_cost_movement_count,
                anomaly_status=self._variance_anomaly_status(
                    movement_count=row.movement_count,
                    shortage_quantity=Decimal(row.shortage_quantity),
                    surplus_quantity=Decimal(row.surplus_quantity),
                    estimated_shortage_value=Decimal(row.estimated_shortage_value),
                    missing_cost_movement_count=row.missing_cost_movement_count,
                ),
                latest_occurred_at=row.latest_occurred_at,
            )
            for row in rows
        ]

    def _variance_anomaly_status(
        self,
        *,
        movement_count: int,
        shortage_quantity: Decimal,
        surplus_quantity: Decimal,
        estimated_shortage_value: Decimal,
        missing_cost_movement_count: int,
    ) -> str:
        if shortage_quantity > 0 and missing_cost_movement_count > 0:
            return "missing_cost"
        if estimated_shortage_value >= self.HIGH_LOSS_VALUE_THRESHOLD:
            return "high_loss"
        if shortage_quantity > 0 and movement_count >= 3:
            return "repeating_loss"
        if shortage_quantity > 0:
            return "watch"
        if surplus_quantity > 0:
            return "surplus_review"
        return "normal"

    def get_variance_period_comparison(
        self,
        *,
        business_unit_id: uuid.UUID | None = None,
        inventory_item_id: uuid.UUID | None = None,
        days: int = 30,
        high_loss_value_threshold: Decimal | None = None,
        worsening_percent_threshold: Decimal | None = None,
    ) -> InventoryVariancePeriodComparison:
        effective_high_loss_threshold = high_loss_value_threshold
        effective_worsening_threshold = worsening_percent_threshold
        if business_unit_id is not None and (
            effective_high_loss_threshold is None
            or effective_worsening_threshold is None
        ):
            threshold = self.get_variance_threshold(business_unit_id=business_unit_id)
            effective_high_loss_threshold = (
                effective_high_loss_threshold or threshold.high_loss_value_threshold
            )
            effective_worsening_threshold = (
                effective_worsening_threshold or threshold.worsening_percent_threshold
            )
        effective_high_loss_threshold = (
            effective_high_loss_threshold or self.HIGH_LOSS_VALUE_THRESHOLD
        )
        effective_worsening_threshold = (
            effective_worsening_threshold or self.WORSENING_PERCENT_THRESHOLD
        )
        current_end_at = datetime.now(UTC)
        current_start_at = current_end_at - timedelta(days=days)
        previous_start_at = current_start_at - timedelta(days=days)
        previous_end_at = current_start_at

        current = self._variance_period_totals(
            business_unit_id=business_unit_id,
            inventory_item_id=inventory_item_id,
            start_at=current_start_at,
            end_at=current_end_at,
        )
        previous = self._variance_period_totals(
            business_unit_id=business_unit_id,
            inventory_item_id=inventory_item_id,
            start_at=previous_start_at,
            end_at=previous_end_at,
        )
        shortage_value_change = (
            current["estimated_shortage_value"] - previous["estimated_shortage_value"]
        )
        shortage_quantity_change = (
            current["shortage_quantity"] - previous["shortage_quantity"]
        )
        movement_count_change = current["movement_count"] - previous["movement_count"]
        change_percent = self._percent_change(
            current=current["estimated_shortage_value"],
            previous=previous["estimated_shortage_value"],
        )
        decision_status, recommendation = self._variance_period_decision(
            current_movement_count=current["movement_count"],
            previous_movement_count=previous["movement_count"],
            current_shortage_value=current["estimated_shortage_value"],
            previous_shortage_value=previous["estimated_shortage_value"],
            current_missing_cost_count=current["missing_cost_movement_count"],
            change_percent=change_percent,
            high_loss_value_threshold=effective_high_loss_threshold,
            worsening_percent_threshold=effective_worsening_threshold,
        )

        return InventoryVariancePeriodComparison(
            current_start_at=current_start_at,
            current_end_at=current_end_at,
            previous_start_at=previous_start_at,
            previous_end_at=previous_end_at,
            period_days=days,
            current_movement_count=current["movement_count"],
            previous_movement_count=previous["movement_count"],
            movement_count_change=movement_count_change,
            current_shortage_quantity=current["shortage_quantity"],
            previous_shortage_quantity=previous["shortage_quantity"],
            shortage_quantity_change=shortage_quantity_change,
            current_estimated_shortage_value=self._money(
                current["estimated_shortage_value"]
            ),
            previous_estimated_shortage_value=self._money(
                previous["estimated_shortage_value"]
            ),
            estimated_shortage_value_change=self._money(shortage_value_change),
            estimated_shortage_value_change_percent=change_percent,
            current_missing_cost_movement_count=current["missing_cost_movement_count"],
            previous_missing_cost_movement_count=previous["missing_cost_movement_count"],
            decision_status=decision_status,
            recommendation=recommendation,
        )

    def _variance_period_totals(
        self,
        *,
        business_unit_id: uuid.UUID | None,
        inventory_item_id: uuid.UUID | None,
        start_at: datetime,
        end_at: datetime,
    ) -> dict[str, Decimal | int]:
        shortage_quantity = sa.case(
            (
                InventoryMovementModel.movement_type == "waste",
                InventoryMovementModel.quantity,
            ),
            else_=0,
        )
        unit_cost = func.coalesce(InventoryItemModel.default_unit_cost, 0)
        shortage_value = sa.case(
            (
                InventoryMovementModel.movement_type == "waste",
                InventoryMovementModel.quantity * unit_cost,
            ),
            else_=0,
        )
        missing_cost_movement = sa.case(
            (
                InventoryItemModel.default_unit_cost.is_(None),
                1,
            ),
            else_=0,
        )
        statement = (
            select(
                func.count(InventoryMovementModel.id).label("movement_count"),
                func.coalesce(func.sum(shortage_quantity), 0).label("shortage_quantity"),
                func.coalesce(func.sum(shortage_value), 0).label(
                    "estimated_shortage_value"
                ),
                func.coalesce(func.sum(missing_cost_movement), 0).label(
                    "missing_cost_movement_count"
                ),
            )
            .select_from(InventoryMovementModel)
            .join(
                InventoryItemModel,
                InventoryItemModel.id == InventoryMovementModel.inventory_item_id,
            )
            .where(InventoryMovementModel.reason_code.is_not(None))
            .where(InventoryMovementModel.movement_type.in_(["adjustment", "waste"]))
            .where(InventoryMovementModel.occurred_at >= start_at)
            .where(InventoryMovementModel.occurred_at < end_at)
        )
        if business_unit_id is not None:
            statement = statement.where(
                InventoryMovementModel.business_unit_id == business_unit_id
            )
        if inventory_item_id is not None:
            statement = statement.where(
                InventoryMovementModel.inventory_item_id == inventory_item_id
            )

        row = self._session.execute(statement).one()
        return {
            "movement_count": int(row.movement_count),
            "shortage_quantity": Decimal(row.shortage_quantity),
            "estimated_shortage_value": Decimal(row.estimated_shortage_value),
            "missing_cost_movement_count": int(row.missing_cost_movement_count),
        }

    def _variance_period_decision(
        self,
        *,
        current_movement_count: int,
        previous_movement_count: int,
        current_shortage_value: Decimal,
        previous_shortage_value: Decimal,
        current_missing_cost_count: int,
        change_percent: Decimal | None,
        high_loss_value_threshold: Decimal,
        worsening_percent_threshold: Decimal,
    ) -> tuple[str, str]:
        if current_movement_count == 0 and previous_movement_count == 0:
            return (
                "stable",
                "Nincs ok-kodos keszletkorrekcio a vizsgalt idoszakokban.",
            )
        if current_missing_cost_count > 0:
            return (
                "missing_cost",
                "Eloszor a hianyzo beszerzesi arakat kell potolni, kulonben a veszteseg HUF becsles torzul.",
            )
        if current_shortage_value >= high_loss_value_threshold:
            return (
                "critical",
                "Magas becsult keszletveszteseg: fizikai ellenorzes, recept/mapping es selejt okok atnezese javasolt.",
            )
        if (
            change_percent is not None
            and change_percent >= worsening_percent_threshold
            and current_shortage_value > previous_shortage_value
        ):
            return (
                "worsening",
                "A becsult veszteseg az elozo idoszakhoz kepest romlik; erdemes a top vesztesegu tetelekre es okokra szurni.",
            )
        if previous_shortage_value > 0 and current_shortage_value < previous_shortage_value:
            return (
                "improving",
                "A becsult veszteseg csokken, de a visszatero okokat tovabbra is figyelni kell.",
            )
        if current_shortage_value > 0 or current_movement_count > 0:
            return (
                "watch",
                "Van keszletkorrekcios aktivitas; a trendet es az ok szerinti bontast erdemes hetente ellenorizni.",
            )
        return (
            "stable",
            "Az aktualis idoszakban nincs becsult veszteseg.",
        )

    def _percent_change(
        self,
        *,
        current: Decimal,
        previous: Decimal,
    ) -> Decimal | None:
        if previous == 0:
            return None
        return ((current - previous) / previous * Decimal("100")).quantize(
            self.PERCENT_QUANT
        )

    def get_variance_threshold(
        self,
        *,
        business_unit_id: uuid.UUID,
    ) -> InventoryVarianceThreshold:
        model = self._session.scalar(
            select(InventoryVarianceThresholdModel).where(
                InventoryVarianceThresholdModel.business_unit_id == business_unit_id
            )
        )
        if model is None:
            return InventoryVarianceThreshold(
                id=None,
                business_unit_id=business_unit_id,
                high_loss_value_threshold=self.HIGH_LOSS_VALUE_THRESHOLD,
                worsening_percent_threshold=self.WORSENING_PERCENT_THRESHOLD,
                is_default=True,
                created_at=None,
                updated_at=None,
            )
        return self._to_variance_threshold_entity(model=model, is_default=False)

    def upsert_variance_threshold(
        self,
        *,
        business_unit_id: uuid.UUID,
        high_loss_value_threshold: Decimal,
        worsening_percent_threshold: Decimal,
    ) -> InventoryVarianceThreshold:
        model = self._session.scalar(
            select(InventoryVarianceThresholdModel).where(
                InventoryVarianceThresholdModel.business_unit_id == business_unit_id
            )
        )
        if model is None:
            model = InventoryVarianceThresholdModel(
                business_unit_id=business_unit_id,
                high_loss_value_threshold=high_loss_value_threshold,
                worsening_percent_threshold=worsening_percent_threshold,
            )
            self._session.add(model)
        else:
            model.high_loss_value_threshold = high_loss_value_threshold
            model.worsening_percent_threshold = worsening_percent_threshold

        self._session.commit()
        self._session.refresh(model)
        return self._to_variance_threshold_entity(model=model, is_default=False)

    @staticmethod
    def _to_variance_threshold_entity(
        *,
        model: InventoryVarianceThresholdModel,
        is_default: bool,
    ) -> InventoryVarianceThreshold:
        return InventoryVarianceThreshold(
            id=model.id,
            business_unit_id=model.business_unit_id,
            high_loss_value_threshold=Decimal(model.high_loss_value_threshold),
            worsening_percent_threshold=Decimal(model.worsening_percent_threshold),
            is_default=is_default,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def _money(value: object) -> Decimal:
        return Decimal(value).quantize(Decimal("0.01"))

    def business_unit_exists(self, business_unit_id: uuid.UUID) -> bool:
        count = self._session.scalar(
            select(func.count())
            .select_from(BusinessUnitModel)
            .where(BusinessUnitModel.id == business_unit_id)
        )
        return bool(count)

    def unit_of_measure_exists(self, uom_id: uuid.UUID) -> bool:
        count = self._session.scalar(
            select(func.count())
            .select_from(UnitOfMeasureModel)
            .where(UnitOfMeasureModel.id == uom_id)
        )
        return bool(count)

    def exists_by_name(
        self,
        *,
        business_unit_id: uuid.UUID,
        name: str,
        exclude_inventory_item_id: uuid.UUID | None = None,
    ) -> bool:
        statement = (
            select(func.count())
            .select_from(InventoryItemModel)
            .where(InventoryItemModel.business_unit_id == business_unit_id)
            .where(InventoryItemModel.name == name)
        )
        if exclude_inventory_item_id is not None:
            statement = statement.where(InventoryItemModel.id != exclude_inventory_item_id)

        count = self._session.scalar(statement)
        return bool(count)

    def get_by_id(self, inventory_item_id: uuid.UUID) -> InventoryItem | None:
        model = self._session.get(InventoryItemModel, inventory_item_id)
        if model is None:
            return None
        return self._to_entity(model)

    def list_stock_levels(
        self,
        *,
        business_unit_id: uuid.UUID | None = None,
        inventory_item_id: uuid.UUID | None = None,
        item_type: str | None = None,
        limit: int = 50,
    ) -> list[InventoryStockLevel]:
        signed_quantity = sa.case(
            (
                InventoryMovementModel.movement_type.in_(
                    ["purchase", "initial_stock", "adjustment"]
                ),
                InventoryMovementModel.quantity,
            ),
            (InventoryMovementModel.movement_type == "waste", -InventoryMovementModel.quantity),
            else_=0,
        )

        statement = (
            select(
                InventoryItemModel.id.label("inventory_item_id"),
                InventoryItemModel.business_unit_id,
                InventoryItemModel.name,
                InventoryItemModel.item_type,
                InventoryItemModel.uom_id,
                InventoryItemModel.track_stock,
                InventoryItemModel.is_active,
                InventoryItemModel.default_unit_cost,
                InventoryItemModel.estimated_stock_quantity,
                func.coalesce(func.sum(signed_quantity), 0).label("current_quantity"),
                func.max(InventoryMovementModel.occurred_at).label("last_movement_at"),
                func.count(InventoryMovementModel.id).label("movement_count"),
            )
            .select_from(InventoryItemModel)
            .outerjoin(
                InventoryMovementModel,
                InventoryMovementModel.inventory_item_id == InventoryItemModel.id,
            )
        )

        if business_unit_id is not None:
            statement = statement.where(
                InventoryItemModel.business_unit_id == business_unit_id
            )
        if inventory_item_id is not None:
            statement = statement.where(InventoryItemModel.id == inventory_item_id)
        if item_type is not None:
            statement = statement.where(InventoryItemModel.item_type == item_type)

        statement = (
            statement.group_by(
                InventoryItemModel.id,
                InventoryItemModel.business_unit_id,
                InventoryItemModel.name,
                InventoryItemModel.item_type,
                InventoryItemModel.uom_id,
                InventoryItemModel.track_stock,
                InventoryItemModel.is_active,
                InventoryItemModel.default_unit_cost,
                InventoryItemModel.estimated_stock_quantity,
            )
            .order_by(InventoryItemModel.name.asc())
            .limit(limit)
        )

        rows = self._session.execute(statement).all()
        return [
            InventoryStockLevel(
                inventory_item_id=row.inventory_item_id,
                business_unit_id=row.business_unit_id,
                name=row.name,
                item_type=row.item_type,
                uom_id=row.uom_id,
                track_stock=row.track_stock,
                is_active=row.is_active,
                default_unit_cost=(
                    Decimal(row.default_unit_cost)
                    if row.default_unit_cost is not None
                    else None
                ),
                estimated_stock_quantity=(
                    Decimal(row.estimated_stock_quantity)
                    if row.estimated_stock_quantity is not None
                    else None
                ),
                current_quantity=Decimal(row.current_quantity),
                last_movement_at=row.last_movement_at,
                movement_count=row.movement_count,
            )
            for row in rows
        ]

    def list_estimated_consumption(
        self,
        *,
        business_unit_id: uuid.UUID | None = None,
        inventory_item_id: uuid.UUID | None = None,
        product_id: uuid.UUID | None = None,
        source_type: str | None = None,
        limit: int = 50,
    ) -> list[EstimatedConsumptionAudit]:
        statement = (
            select(
                EstimatedConsumptionAuditModel,
                ProductModel.name.label("product_name"),
                InventoryItemModel.name.label("inventory_item_name"),
                UnitOfMeasureModel.code.label("uom_code"),
            )
            .join(ProductModel, ProductModel.id == EstimatedConsumptionAuditModel.product_id)
            .join(
                InventoryItemModel,
                InventoryItemModel.id == EstimatedConsumptionAuditModel.inventory_item_id,
            )
            .join(UnitOfMeasureModel, UnitOfMeasureModel.id == EstimatedConsumptionAuditModel.uom_id)
        )

        if business_unit_id is not None:
            statement = statement.where(
                EstimatedConsumptionAuditModel.business_unit_id == business_unit_id
            )
        if inventory_item_id is not None:
            statement = statement.where(
                EstimatedConsumptionAuditModel.inventory_item_id == inventory_item_id
            )
        if product_id is not None:
            statement = statement.where(
                EstimatedConsumptionAuditModel.product_id == product_id
            )
        if source_type is not None:
            statement = statement.where(
                EstimatedConsumptionAuditModel.source_type == source_type
            )

        rows = self._session.execute(
            statement.order_by(
                EstimatedConsumptionAuditModel.occurred_at.desc(),
                EstimatedConsumptionAuditModel.created_at.desc(),
            ).limit(limit)
        ).all()

        return [
            EstimatedConsumptionAudit(
                id=model.id,
                business_unit_id=model.business_unit_id,
                product_id=model.product_id,
                product_name=product_name,
                inventory_item_id=model.inventory_item_id,
                inventory_item_name=inventory_item_name,
                recipe_version_id=model.recipe_version_id,
                source_type=model.source_type,
                source_id=model.source_id,
                source_dedupe_key=model.source_dedupe_key,
                receipt_no=model.receipt_no,
                estimation_basis=model.estimation_basis,
                quantity=Decimal(model.quantity),
                uom_id=model.uom_id,
                uom_code=uom_code,
                quantity_before=Decimal(model.quantity_before),
                quantity_after=Decimal(model.quantity_after),
                occurred_at=model.occurred_at,
                created_at=model.created_at,
            )
            for model, product_name, inventory_item_name, uom_code in rows
        ]

    @staticmethod
    def _to_entity(model: InventoryItemModel) -> InventoryItem:
        return InventoryItem(
            id=model.id,
            business_unit_id=model.business_unit_id,
            name=model.name,
            item_type=model.item_type,
            uom_id=model.uom_id,
            track_stock=model.track_stock,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def _to_movement_entity(model: InventoryMovementModel) -> InventoryMovement:
        unit_cost = None
        if model.unit_cost is not None:
            unit_cost = Decimal(model.unit_cost)

        return InventoryMovement(
            id=model.id,
            business_unit_id=model.business_unit_id,
            inventory_item_id=model.inventory_item_id,
            movement_type=model.movement_type,
            quantity=Decimal(model.quantity),
            uom_id=model.uom_id,
            unit_cost=unit_cost,
            reason_code=model.reason_code,
            note=model.note,
            source_type=model.source_type,
            source_id=model.source_id,
            occurred_at=model.occurred_at,
            created_at=model.created_at,
        )
