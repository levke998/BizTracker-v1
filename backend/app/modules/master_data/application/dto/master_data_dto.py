"""DTOs used by master data query use cases."""

from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BusinessUnitDto:
    id: uuid.UUID
    code: str
    name: str
    type: str
    is_active: bool


@dataclass(frozen=True, slots=True)
class LocationDto:
    id: uuid.UUID
    business_unit_id: uuid.UUID
    name: str
    kind: str
    is_active: bool


@dataclass(frozen=True, slots=True)
class UnitOfMeasureDto:
    id: uuid.UUID
    code: str
    name: str
    symbol: str | None


@dataclass(frozen=True, slots=True)
class CategoryDto:
    id: uuid.UUID
    business_unit_id: uuid.UUID
    parent_id: uuid.UUID | None
    name: str
    is_active: bool


@dataclass(frozen=True, slots=True)
class ProductDto:
    id: uuid.UUID
    business_unit_id: uuid.UUID
    category_id: uuid.UUID | None
    sku: str | None
    name: str
    product_type: str
    is_active: bool
