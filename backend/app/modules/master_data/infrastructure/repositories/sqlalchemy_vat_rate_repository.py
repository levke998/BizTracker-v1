"""SQLAlchemy VAT rate repository."""

from __future__ import annotations

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.modules.master_data.domain.entities.vat_rate import VatRate
from app.modules.master_data.infrastructure.orm.vat_rate_model import VatRateModel


class SqlAlchemyVatRateRepository:
    """SQLAlchemy-backed VAT rate repository."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def list_all(self, *, active_only: bool = True) -> list[VatRate]:
        statement: Select[tuple[VatRateModel]] = select(VatRateModel)
        if active_only:
            statement = statement.where(VatRateModel.is_active.is_(True))
        statement = statement.order_by(
            VatRateModel.rate_percent.desc(),
            VatRateModel.code.asc(),
        )
        items = self._session.scalars(statement).all()
        return [self._to_entity(item) for item in items]

    @staticmethod
    def _to_entity(model: VatRateModel) -> VatRate:
        return VatRate(
            id=model.id,
            code=model.code,
            name=model.name,
            rate_percent=model.rate_percent,
            rate_type=model.rate_type,
            nav_code=model.nav_code,
            description=model.description,
            valid_from=model.valid_from,
            valid_to=model.valid_to,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
