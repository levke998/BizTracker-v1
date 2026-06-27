"""SQLAlchemy event cost line repository."""

from __future__ import annotations

import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.modules.events.domain.entities.event_cost import EventCostLine, NewEventCostLine
from app.modules.events.infrastructure.orm.event_cost_model import EventCostLineModel
from app.modules.events.infrastructure.orm.event_model import EventModel


class SqlAlchemyEventCostRepository:
    """SQLAlchemy-backed event cost repository."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def list_by_event_id(self, event_id: uuid.UUID) -> list[EventCostLine]:
        models = self._session.scalars(
            select(EventCostLineModel)
            .where(EventCostLineModel.event_id == event_id)
            .order_by(EventCostLineModel.incurred_at.asc().nulls_last(), EventCostLineModel.created_at.asc())
        ).all()
        return [self._to_entity(model) for model in models]

    def replace_for_event(
        self,
        *,
        event_id: uuid.UUID,
        cost_lines: list[NewEventCostLine],
    ) -> list[EventCostLine]:
        self._session.execute(
            delete(EventCostLineModel).where(EventCostLineModel.event_id == event_id)
        )
        models = [
            EventCostLineModel(
                event_id=event_id,
                category=cost_line.category,
                description=cost_line.description,
                amount_gross=cost_line.amount_gross,
                source_type=cost_line.source_type,
                source_reference=cost_line.source_reference,
                incurred_at=cost_line.incurred_at,
                notes=cost_line.notes,
            )
            for cost_line in cost_lines
        ]
        self._session.add_all(models)
        self._session.commit()
        for model in models:
            self._session.refresh(model)
        return [self._to_entity(model) for model in models]

    def event_exists(self, event_id: uuid.UUID) -> bool:
        count = self._session.scalar(
            select(func.count()).select_from(EventModel).where(EventModel.id == event_id)
        )
        return bool(count)

    @staticmethod
    def _to_entity(model: EventCostLineModel) -> EventCostLine:
        return EventCostLine(
            id=model.id,
            event_id=model.event_id,
            category=model.category,
            description=model.description,
            amount_gross=model.amount_gross,
            source_type=model.source_type,
            source_reference=model.source_reference,
            incurred_at=model.incurred_at,
            notes=model.notes,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
