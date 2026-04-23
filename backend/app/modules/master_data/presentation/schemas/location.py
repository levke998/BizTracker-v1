"""Location response schema."""

from __future__ import annotations

import uuid

from app.modules.master_data.presentation.schemas.common import MasterDataBaseSchema


class LocationResponse(MasterDataBaseSchema):
    """Read-only location response."""

    id: uuid.UUID
    business_unit_id: uuid.UUID
    name: str
    kind: str
    is_active: bool
