"""DTOs used by master data query use cases."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal


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
class VatRateDto:
    id: uuid.UUID
    code: str
    name: str
    rate_percent: Decimal
    rate_type: str
    nav_code: str | None
    description: str | None
    valid_from: date | None
    valid_to: date | None
    is_active: bool


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
    sales_uom_id: uuid.UUID | None
    default_vat_rate_id: uuid.UUID | None
    sku: str | None
    name: str
    product_type: str
    sale_price_gross: Decimal | None
    sale_price_last_seen_at: datetime | None
    sale_price_source: str | None
    default_unit_cost: Decimal | None
    currency: str
    is_active: bool
