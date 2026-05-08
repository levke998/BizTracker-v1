"""SQLAlchemy event repository."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.events.domain.entities.event import Event, NewEvent
from app.modules.events.infrastructure.orm.event_model import EventModel
from app.modules.master_data.infrastructure.orm.business_unit_model import (
    BusinessUnitModel,
)
from app.modules.master_data.infrastructure.orm.location_model import LocationModel


class SqlAlchemyEventRepository:
    """SQLAlchemy repository for event planning data."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, event_id: uuid.UUID) -> Event | None:
        model = self._session.get(EventModel, event_id)
        if model is None:
            return None
        return self._to_entity(model)

    def list_many(
        self,
        *,
        business_unit_id: uuid.UUID | None = None,
        status: str | None = None,
        is_active: bool | None = None,
        starts_from: datetime | None = None,
        starts_to: datetime | None = None,
        limit: int = 50,
    ) -> list[Event]:
        statement = select(EventModel)

        if business_unit_id is not None:
            statement = statement.where(EventModel.business_unit_id == business_unit_id)
        if status is not None:
            statement = statement.where(EventModel.status == status)
        if is_active is not None:
            statement = statement.where(EventModel.is_active == is_active)
        if starts_from is not None:
            statement = statement.where(EventModel.starts_at >= starts_from)
        if starts_to is not None:
            statement = statement.where(EventModel.starts_at <= starts_to)

        statement = statement.order_by(EventModel.starts_at.desc()).limit(limit)
        models = self._session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def create(self, event: NewEvent) -> Event:
        model = EventModel(**self._model_values(event))
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return self._to_entity(model)

    def update(self, event_id: uuid.UUID, event: NewEvent) -> Event | None:
        model = self._session.get(EventModel, event_id)
        if model is None:
            return None

        for key, value in self._model_values(event).items():
            setattr(model, key, value)
        self._session.commit()
        self._session.refresh(model)
        return self._to_entity(model)

    def archive(self, event_id: uuid.UUID) -> Event | None:
        model = self._session.get(EventModel, event_id)
        if model is None:
            return None

        model.is_active = False
        model.status = "cancelled" if model.status in {"planned", "confirmed"} else model.status
        self._session.commit()
        self._session.refresh(model)
        return self._to_entity(model)

    def business_unit_exists(self, business_unit_id: uuid.UUID) -> bool:
        count = self._session.scalar(
            select(func.count())
            .select_from(BusinessUnitModel)
            .where(BusinessUnitModel.id == business_unit_id)
        )
        return bool(count)

    def location_belongs_to_business_unit(
        self,
        *,
        location_id: uuid.UUID,
        business_unit_id: uuid.UUID,
    ) -> bool:
        count = self._session.scalar(
            select(func.count())
            .select_from(LocationModel)
            .where(LocationModel.id == location_id)
            .where(LocationModel.business_unit_id == business_unit_id)
        )
        return bool(count)

    @staticmethod
    def _model_values(event: NewEvent) -> dict[str, object]:
        return {
            "business_unit_id": event.business_unit_id,
            "location_id": event.location_id,
            "title": event.title,
            "status": event.status,
            "starts_at": event.starts_at,
            "ends_at": event.ends_at,
            "performer_name": event.performer_name,
            "expected_attendance": event.expected_attendance,
            "ticket_revenue_gross": event.ticket_revenue_gross,
            "bar_revenue_gross": event.bar_revenue_gross,
            "performer_share_percent": event.performer_share_percent,
            "performer_fixed_fee": event.performer_fixed_fee,
            "event_cost_amount": event.event_cost_amount,
            "notes": event.notes,
            "is_active": event.is_active,
        }

    @staticmethod
    def _to_entity(model: EventModel) -> Event:
        return Event(
            id=model.id,
            business_unit_id=model.business_unit_id,
            location_id=model.location_id,
            title=model.title,
            status=model.status,
            starts_at=model.starts_at,
            ends_at=model.ends_at,
            performer_name=model.performer_name,
            expected_attendance=model.expected_attendance,
            ticket_revenue_gross=model.ticket_revenue_gross,
            bar_revenue_gross=model.bar_revenue_gross,
            performer_share_percent=model.performer_share_percent,
            performer_fixed_fee=model.performer_fixed_fee,
            event_cost_amount=model.event_cost_amount,
            notes=model.notes,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
