"""Stable POS sale identity helpers shared by API and CSV ingestion."""

from __future__ import annotations

import hashlib
import json
import uuid
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping


def build_pos_sale_dedupe_key(
    *,
    business_unit_id: uuid.UUID,
    payload: Mapping[str, Any],
) -> str:
    """Build a stable line-level identity for the same POS sale across sources."""

    components = {
        "business_unit_id": str(business_unit_id),
        "date": _normalize_text(payload.get("date")),
        "receipt_no": _normalize_text(payload.get("receipt_no")),
        "product_name": _normalize_text(payload.get("product_name")),
        "quantity": _normalize_decimal(payload.get("quantity"), places="0.001"),
        "gross_amount": _normalize_decimal(payload.get("gross_amount"), places="0.01"),
    }
    source_line_key = _normalize_text(payload.get("source_line_key"))
    if source_line_key:
        components["source_line_key"] = source_line_key
    serialized = json.dumps(components, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def _normalize_decimal(value: Any, *, places: str) -> str:
    if value is None:
        return "0"
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return str(value).strip()
    return str(parsed.quantize(Decimal(places)))
