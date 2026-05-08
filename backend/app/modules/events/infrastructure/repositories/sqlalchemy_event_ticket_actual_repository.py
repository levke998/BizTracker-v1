"""SQLAlchemy event ticket actual repository."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.events.domain.entities.event_ticket_actual import (
    EventTicketActual,
    NewEventTicketActual,
)
from app.modules.events.infrastructure.orm.event_model import EventModel
from app.modules.events.infrastructure.orm.event_ticket_actual_model import (
    EventTicketActualModel,
)
from app.modules.master_data.infrastructure.orm.vat_rate_model import VatRateModel


class SqlAlchemyEventTicketActualRepository:
    """SQLAlchemy-backed ticket actual repository."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_event_id(self, event_id: uuid.UUID) -> EventTicketActual | None:
        model = self._session.scalar(
            select(EventTicketActualModel).where(EventTicketActualModel.event_id == event_id)
        )
        if model is None:
            return None
        return self._to_entity(model)

    def upsert(self, actual: NewEventTicketActual) -> EventTicketActual:
        model = self._session.scalar(
            select(EventTicketActualModel).where(
                EventTicketActualModel.event_id == actual.event_id
            )
        )
        if model is None:
            model = EventTicketActualModel(event_id=actual.event_id)
            self._session.add(model)

        for key, value in self._model_values(actual).items():
            setattr(model, key, value)

        self._session.commit()
        self._session.refresh(model)
        return self._to_entity(model)

    def event_exists(self, event_id: uuid.UUID) -> bool:
        count = self._session.scalar(
            select(func.count()).select_from(EventModel).where(EventModel.id == event_id)
        )
        return bool(count)

    def vat_rate_exists(self, vat_rate_id: uuid.UUID) -> bool:
        count = self._session.scalar(
            select(func.count()).select_from(VatRateModel).where(VatRateModel.id == vat_rate_id)
        )
        return bool(count)

    @staticmethod
    def _model_values(actual: NewEventTicketActual) -> dict[str, object]:
        return {
            "source_name": actual.source_name,
            "source_reference": actual.source_reference,
            "sold_quantity": actual.sold_quantity,
            "gross_revenue": actual.gross_revenue,
            "net_revenue": actual.net_revenue,
            "vat_amount": actual.vat_amount,
            "vat_rate_id": actual.vat_rate_id,
            "platform_fee_gross": actual.platform_fee_gross,
            "reported_at": actual.reported_at,
            "notes": actual.notes,
        }

    @staticmethod
    def _to_entity(model: EventTicketActualModel) -> EventTicketActual:
        return EventTicketActual(
            id=model.id,
            event_id=model.event_id,
            source_name=model.source_name,
            source_reference=model.source_reference,
            sold_quantity=model.sold_quantity,
            gross_revenue=model.gross_revenue,
            net_revenue=model.net_revenue,
            vat_amount=model.vat_amount,
            vat_rate_id=model.vat_rate_id,
            platform_fee_gross=model.platform_fee_gross,
            reported_at=model.reported_at,
            notes=model.notes,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
