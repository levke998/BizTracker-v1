"""Unit tests for pure forecast demand statistics and recommendations."""

from __future__ import annotations

from decimal import Decimal

from app.modules.analytics.infrastructure.repositories.forecast_demand_rules import (
    average_decimal,
    average_revenue_by_key,
    average_sales_by_key,
    average_window_sales_by_key,
    category_recommendation,
    demand_signal,
    dominant_label,
    dominant_product_categories,
    impact_recommendation,
    peak_time_recommendation,
    product_recommendation,
)


def test_baseline_helpers_average_each_requested_metric() -> None:
    rows = [
        {
            "key": "A",
            "product_name": "Latte",
            "category_name": "Kávé",
            "revenue": Decimal("100"),
            "quantity": Decimal("2"),
            "transaction_count": Decimal("1"),
        },
        {
            "key": "A",
            "product_name": "Latte",
            "category_name": "Kávé",
            "revenue": Decimal("300"),
            "quantity": Decimal("4"),
            "transaction_count": Decimal("3"),
        },
    ]

    assert average_decimal([Decimal("100"), Decimal("300")]) == Decimal("200")
    assert average_revenue_by_key(
        rows,
        key_builder=lambda row: row["key"],
    ) == {"A": Decimal("200")}
    assert average_sales_by_key(
        rows,
        key_builder=lambda row: row["key"],
    ) == {"A": {"revenue": Decimal("200"), "quantity": Decimal("3")}}
    assert average_window_sales_by_key(
        rows,
        key_builder=lambda row: row["key"],
    ) == {
        "A": {
            "revenue": Decimal("200"),
            "quantity": Decimal("3"),
            "transaction_count": Decimal("2"),
        }
    }
    assert dominant_product_categories(rows, fallback="Ismeretlen") == {
        "Latte": "Kávé"
    }


def test_demand_signal_boundaries_are_explicit() -> None:
    assert demand_signal(Decimal("20")) == "emelkedo"
    assert demand_signal(Decimal("19.99")) == "normal"
    assert demand_signal(Decimal("-15")) == "visszafogott"
    assert demand_signal(Decimal("-14.99")) == "normal"
    assert dominant_label({}, fallback="ismeretlen") == "ismeretlen"


def test_recommendations_cover_business_specific_branches() -> None:
    assert "Kánikula" in impact_recommendation(
        scope="gourmand",
        temperature_band="kanikula",
        condition_band="napos_szaraz",
        expected_revenue=Decimal("100"),
        historical_average=Decimal("100"),
    )
    assert "fagylalt" in category_recommendation(
        category_name="Fagylalt",
        temperature_band="meleg",
        condition_band="napos_szaraz",
        signal="emelkedo",
    )
    assert "pultfeltöltés" in product_recommendation(
        product_name="Latte",
        signal="emelkedo",
        condition_band="napos_szaraz",
    )
    assert "személyzet" in peak_time_recommendation(
        time_window="Délután",
        signal="emelkedo",
    )
