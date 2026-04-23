"""Shared response schema helpers for the master data module."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class MasterDataBaseSchema(BaseModel):
    """Base schema configured for attribute-based validation."""

    model_config = ConfigDict(from_attributes=True)
