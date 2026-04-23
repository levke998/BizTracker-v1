"""Unit-of-measure response schema."""

from __future__ import annotations

import uuid

from app.modules.master_data.presentation.schemas.common import MasterDataBaseSchema


class UnitOfMeasureResponse(MasterDataBaseSchema):
    """Read-only unit-of-measure response."""

    id: uuid.UUID
    code: str
    name: str
    symbol: str | None
