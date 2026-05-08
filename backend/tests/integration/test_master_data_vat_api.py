"""Integration tests for VAT master data APIs."""

from __future__ import annotations

from decimal import Decimal

from fastapi.testclient import TestClient


def test_list_vat_rates_returns_hungarian_reference_rates(client: TestClient) -> None:
    response = client.get("/api/v1/master-data/vat-rates")

    assert response.status_code == 200
    payload = response.json()
    rates_by_code = {item["code"]: item for item in payload}

    assert {"HU_27", "HU_18", "HU_5", "HU_0"}.issubset(rates_by_code)
    assert Decimal(rates_by_code["HU_27"]["rate_percent"]) == Decimal("27.0000")
    assert Decimal(rates_by_code["HU_0"]["rate_percent"]) == Decimal("0.0000")
    assert rates_by_code["HU_27"]["is_active"] is True
