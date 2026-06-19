"""Domain model for POS source product mappings."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime
import uuid


@dataclass(slots=True)
class PosProductAlias:
    """One reviewable link between a POS source key and an internal product."""

    id: uuid.UUID
    business_unit_id: uuid.UUID
    product_id: uuid.UUID | None
    source_system: str
    source_product_key: str
    source_product_name: str
    source_sku: str | None
    source_barcode: str | None
    status: str
    mapping_confidence: str
    occurrence_count: int
    first_seen_at: datetime | None
    last_seen_at: datetime | None
    last_import_batch_id: uuid.UUID | None
    last_import_row_id: uuid.UUID | None
    notes: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    def approve(self, *, product_id: uuid.UUID, notes: str | None = None) -> None:
        """Apply a user-reviewed product mapping."""

        self.product_id = product_id
        self.status = "mapped"
        self.mapping_confidence = "manual"
        self.notes = notes.strip() if notes and notes.strip() else None
        self.is_active = True


@dataclass(frozen=True, slots=True)
class PosMappingReadiness:
    """Traffic-weighted readiness of POS source product mappings."""

    status: str
    alias_coverage_percent: Decimal
    row_coverage_percent: Decimal
    gross_revenue_coverage_percent: Decimal
    total_alias_count: int
    mapped_alias_count: int
    automatic_alias_count: int
    missing_alias_count: int
    total_row_count: int
    mapped_row_count: int
    automatic_row_count: int
    missing_row_count: int
    total_gross_revenue: Decimal
    mapped_gross_revenue: Decimal
    automatic_gross_revenue: Decimal
    missing_gross_revenue: Decimal
    source_layer: str = "pos_import_rows"
