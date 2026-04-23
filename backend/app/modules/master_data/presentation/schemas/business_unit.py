"""Business unit response schema."""

from __future__ import annotations

import uuid

from app.modules.master_data.presentation.schemas.common import MasterDataBaseSchema


class BusinessUnitResponse(MasterDataBaseSchema):
    """Read-only business unit response."""

    id: uuid.UUID
    code: str
    name: str
    type: str
    is_active: bool
