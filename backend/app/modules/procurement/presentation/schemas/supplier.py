"""Supplier request and response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SupplierCreateRequest(BaseModel):
    """Create request for one supplier."""

    business_unit_id: uuid.UUID
    name: str = Field(min_length=1, max_length=180)
    tax_id: str | None = Field(default=None, max_length=80)
    contact_name: str | None = Field(default=None, max_length=150)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=80)
    notes: str | None = Field(default=None, max_length=1000)
    is_active: bool = True


class SupplierResponse(BaseModel):
    """Read model for one supplier."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    business_unit_id: uuid.UUID
    name: str
    tax_id: str | None
    contact_name: str | None
    email: str | None
    phone: str | None
    notes: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
