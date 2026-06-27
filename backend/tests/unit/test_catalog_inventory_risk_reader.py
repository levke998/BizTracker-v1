"""Unit tests for catalog and inventory risk rules."""

from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

from app.modules.analytics.infrastructure.repositories.catalog_inventory_risk_reader import (
    CatalogInventoryRiskReader,
)


def test_quantity_conversion_handles_supported_mass_units() -> None:
    assert CatalogInventoryRiskReader._convert_quantity(
        Decimal("500"),
        from_uom="g",
        to_uom="kg",
    ) == Decimal("0.500")


def test_stock_risk_score_marks_no_actual_stock_as_danger() -> None:
    item = SimpleNamespace(estimated_stock_quantity=None)

    reasons, score = CatalogInventoryRiskReader._stock_risk_score(
        item=item,
        current=Decimal("0"),
        movement_count=0,
        used_by=2,
    )

    assert "Nincs készletmozgás" in reasons
    assert "Nincs tényleges készlet" in reasons
    assert "Hiányzó becsült készlet" in reasons
    assert score >= 80
