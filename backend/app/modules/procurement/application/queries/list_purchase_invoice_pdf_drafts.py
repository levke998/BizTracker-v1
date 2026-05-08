"""List uploaded supplier invoice PDF drafts."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.procurement.infrastructure.orm.purchase_invoice_draft_model import (
    PurchaseInvoiceDraftModel,
)


class ListPurchaseInvoicePdfDraftsQuery:
    """Return PDF invoice drafts for review screens."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def execute(
        self,
        *,
        business_unit_id: uuid.UUID | None = None,
        limit: int = 50,
    ) -> list[PurchaseInvoiceDraftModel]:
        statement = select(PurchaseInvoiceDraftModel).order_by(
            PurchaseInvoiceDraftModel.created_at.desc(),
            PurchaseInvoiceDraftModel.original_name.asc(),
        )
        if business_unit_id is not None:
            statement = statement.where(
                PurchaseInvoiceDraftModel.business_unit_id == business_unit_id
            )
        return list(self._session.scalars(statement.limit(limit)).all())
