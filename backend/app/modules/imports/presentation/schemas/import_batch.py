"""Import batch response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ImportSchemaBase(BaseModel):
    """Base schema for import responses."""

    model_config = ConfigDict(from_attributes=True)


class ImportFileResponse(ImportSchemaBase):
    """Metadata for one uploaded file."""

    id: uuid.UUID
    batch_id: uuid.UUID
    original_name: str
    stored_path: str
    mime_type: str | None
    size_bytes: int
    uploaded_at: datetime


class ImportBatchResponse(ImportSchemaBase):
    """Read-only import batch response."""

    id: uuid.UUID
    business_unit_id: uuid.UUID
    import_type: str
    status: str
    started_at: datetime
    finished_at: datetime | None
    total_rows: int
    parsed_rows: int
    error_rows: int
    created_at: datetime
    updated_at: datetime
    files: list[ImportFileResponse]
