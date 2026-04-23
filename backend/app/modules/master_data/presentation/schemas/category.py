"""Category response schema."""

from __future__ import annotations

import uuid

from app.modules.master_data.presentation.schemas.common import MasterDataBaseSchema


class CategoryResponse(MasterDataBaseSchema):
    """Read-only category response."""

    id: uuid.UUID
    business_unit_id: uuid.UUID
    parent_id: uuid.UUID | None
    name: str
    is_active: bool
