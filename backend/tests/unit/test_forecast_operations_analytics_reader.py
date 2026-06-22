"""Unit tests for operational forecast readiness rules."""

from __future__ import annotations

from decimal import Decimal

from app.modules.analytics.infrastructure.repositories.forecast_operations_analytics_reader import (
    flow_event_focus_area,
    flow_event_preparation_level,
    flow_event_recommendation,
    preparation_readiness,
    preparation_recommendation,
    readiness_rank,
)


def test_preparation_readiness_prioritizes_missing_stock() -> None:
    assert preparation_readiness(
        demand_signal="normal",
        confidence="magas",
        product_count=2,
        risky_product_count=1,
        low_stock_count=0,
        missing_stock_count=1,
    ) == "kritikus"
    assert readiness_rank("kritikus") > readiness_rank("figyelendo")
    assert "hiányzik" in preparation_recommendation(
        category_name="Fagyi",
        demand_signal="normal",
        readiness_level="kritikus",
        risky_product_count=1,
        low_stock_count=0,
        missing_stock_count=1,
    )


def test_flow_event_rules_identify_rain_as_operational_risk() -> None:
    level = flow_event_preparation_level(
        condition_band="csapadekos",
        precipitation=Decimal("2.5"),
        average_wind=Decimal("10"),
        expected_attendance=260,
    )
    focus = flow_event_focus_area(
        condition_band="csapadekos",
        average_temperature=Decimal("12"),
        precipitation=Decimal("2.5"),
        average_wind=Decimal("10"),
        expected_attendance=260,
    )
    recommendation = flow_event_recommendation(
        title="Koncert",
        condition_band="csapadekos",
        average_temperature=Decimal("12"),
        precipitation=Decimal("2.5"),
        average_wind=Decimal("10"),
        expected_attendance=260,
        preparation_level=level,
    )

    assert level == "kritikus"
    assert focus == "Beléptetés, ruhatár és fedett sor"
    assert "fedett sor" in recommendation
