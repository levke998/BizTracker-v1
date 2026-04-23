"""Finance SQLAlchemy repository."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.finance.domain.entities.transaction import (
    FinancialTransaction,
    NewFinancialTransaction,
)
from app.modules.finance.infrastructure.orm.transaction_model import (
    FinancialTransactionModel,
)


class SqlAlchemyFinancialTransactionRepository:
    """SQLAlchemy-backed repository for finance transactions."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create_many(
        self,
        transactions: list[NewFinancialTransaction],
    ) -> list[FinancialTransaction]:
        if not transactions:
            return []

        try:
            models = [
                FinancialTransactionModel(
                    business_unit_id=transaction.business_unit_id,
                    direction=transaction.direction,
                    transaction_type=transaction.transaction_type,
                    amount=transaction.amount,
                    currency=transaction.currency,
                    occurred_at=transaction.occurred_at,
                    description=transaction.description,
                    source_type=transaction.source_type,
                    source_id=transaction.source_id,
                )
                for transaction in transactions
            ]
            self._session.add_all(models)
            self._session.commit()
        except Exception:
            self._session.rollback()
            raise

        for model in models:
            self._session.refresh(model)

        return [self._to_entity(model) for model in models]

    def has_source_references(
        self,
        *,
        source_type: str,
        source_ids: list[uuid.UUID],
    ) -> bool:
        if not source_ids:
            return False

        count = self._session.scalar(
            select(func.count())
            .select_from(FinancialTransactionModel)
            .where(FinancialTransactionModel.source_type == source_type)
            .where(FinancialTransactionModel.source_id.in_(source_ids))
        )
        return bool(count)

    def list_many(
        self,
        *,
        business_unit_id: uuid.UUID | None = None,
        transaction_type: str | None = None,
        source_type: str | None = None,
        limit: int = 50,
    ) -> list[FinancialTransaction]:
        statement = select(FinancialTransactionModel)

        if business_unit_id is not None:
            statement = statement.where(
                FinancialTransactionModel.business_unit_id == business_unit_id
            )
        if transaction_type is not None:
            statement = statement.where(
                FinancialTransactionModel.transaction_type == transaction_type
            )
        if source_type is not None:
            statement = statement.where(FinancialTransactionModel.source_type == source_type)

        statement = statement.order_by(FinancialTransactionModel.occurred_at.desc()).limit(
            limit
        )
        models = self._session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    @staticmethod
    def _to_entity(model: FinancialTransactionModel) -> FinancialTransaction:
        return FinancialTransaction(
            id=model.id,
            business_unit_id=model.business_unit_id,
            direction=model.direction,
            transaction_type=model.transaction_type,
            amount=model.amount,
            currency=model.currency,
            occurred_at=model.occurred_at,
            description=model.description,
            source_type=model.source_type,
            source_id=model.source_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
