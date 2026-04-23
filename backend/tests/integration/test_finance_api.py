"""Integration tests for finance read APIs."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient

from app.modules.master_data.infrastructure.orm.business_unit_model import (
    BusinessUnitModel,
)

API_PREFIX = "/api/v1/finance"


def test_list_financial_transactions_returns_successful_result(
    client: TestClient,
    create_financial_transaction,
    test_business_unit: BusinessUnitModel,
) -> None:
    transaction = create_financial_transaction(
        business_unit_id=test_business_unit.id,
        transaction_type="pos_sale",
        source_type="import_row",
        occurred_at=datetime(2026, 4, 23, 10, 0, tzinfo=UTC),
        amount=Decimal("1200.00"),
        description="Croissant (RCPT-1001)",
    )

    response = client.get(
        f"{API_PREFIX}/transactions",
        params={"business_unit_id": str(test_business_unit.id)},
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) >= 1
    assert payload[0]["id"] == str(transaction.id)
    assert payload[0]["business_unit_id"] == str(test_business_unit.id)
    assert payload[0]["direction"] == "inflow"
    assert payload[0]["transaction_type"] == "pos_sale"
    assert payload[0]["amount"] == "1200.00"
    assert payload[0]["currency"] == "HUF"
    assert payload[0]["source_type"] == "import_row"


def test_list_financial_transactions_filters_by_business_unit(
    client: TestClient,
    create_financial_transaction,
    test_business_unit: BusinessUnitModel,
) -> None:
    create_financial_transaction(
        business_unit_id=test_business_unit.id,
        transaction_type="pos_sale",
        source_type="import_row",
        occurred_at=datetime(2026, 4, 23, 10, 0, tzinfo=UTC),
        amount=Decimal("1200.00"),
        description="Transaction A",
    )

    response = client.get(
        f"{API_PREFIX}/transactions",
        params={"business_unit_id": str(test_business_unit.id)},
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["business_unit_id"] == str(test_business_unit.id)

    empty_response = client.get(
        f"{API_PREFIX}/transactions",
        params={"business_unit_id": str(uuid4())},
    )

    assert empty_response.status_code == 200
    assert empty_response.json() == []


def test_list_financial_transactions_filters_by_transaction_type(
    client: TestClient,
    create_financial_transaction,
    test_business_unit: BusinessUnitModel,
) -> None:
    create_financial_transaction(
        business_unit_id=test_business_unit.id,
        transaction_type="pos_sale",
        source_type="import_row",
        occurred_at=datetime(2026, 4, 23, 10, 0, tzinfo=UTC),
        amount=Decimal("1200.00"),
        description="POS transaction",
    )
    create_financial_transaction(
        business_unit_id=test_business_unit.id,
        transaction_type="manual_adjustment",
        source_type="manual_entry",
        occurred_at=datetime(2026, 4, 23, 11, 0, tzinfo=UTC),
        amount=Decimal("999.00"),
        description="Manual transaction",
    )

    response = client.get(
        f"{API_PREFIX}/transactions",
        params={
            "business_unit_id": str(test_business_unit.id),
            "transaction_type": "pos_sale",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["transaction_type"] == "pos_sale"


def test_list_financial_transactions_filters_by_source_type(
    client: TestClient,
    create_financial_transaction,
    test_business_unit: BusinessUnitModel,
) -> None:
    create_financial_transaction(
        business_unit_id=test_business_unit.id,
        transaction_type="pos_sale",
        source_type="import_row",
        occurred_at=datetime(2026, 4, 23, 10, 0, tzinfo=UTC),
        amount=Decimal("1200.00"),
        description="Imported transaction",
    )
    create_financial_transaction(
        business_unit_id=test_business_unit.id,
        transaction_type="pos_sale",
        source_type="manual_entry",
        occurred_at=datetime(2026, 4, 23, 11, 0, tzinfo=UTC),
        amount=Decimal("999.00"),
        description="Manual transaction",
    )

    response = client.get(
        f"{API_PREFIX}/transactions",
        params={
            "business_unit_id": str(test_business_unit.id),
            "source_type": "import_row",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["source_type"] == "import_row"


def test_list_financial_transactions_are_sorted_by_occurred_at_desc(
    client: TestClient,
    create_financial_transaction,
    test_business_unit: BusinessUnitModel,
) -> None:
    create_financial_transaction(
        business_unit_id=test_business_unit.id,
        transaction_type="pos_sale",
        source_type="import_row",
        occurred_at=datetime(2026, 4, 23, 9, 0, tzinfo=UTC),
        amount=Decimal("100.00"),
        description="Older transaction",
    )
    newer_transaction = create_financial_transaction(
        business_unit_id=test_business_unit.id,
        transaction_type="pos_sale",
        source_type="import_row",
        occurred_at=datetime(2026, 4, 23, 12, 0, tzinfo=UTC),
        amount=Decimal("200.00"),
        description="Newer transaction",
    )

    response = client.get(
        f"{API_PREFIX}/transactions",
        params={"business_unit_id": str(test_business_unit.id)},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload[0]["id"] == str(newer_transaction.id)
    assert payload[0]["occurred_at"] >= payload[1]["occurred_at"]


def test_list_financial_transactions_respects_limit(
    client: TestClient,
    create_financial_transaction,
    test_business_unit: BusinessUnitModel,
) -> None:
    for index in range(3):
        create_financial_transaction(
            business_unit_id=test_business_unit.id,
            transaction_type="pos_sale",
            source_type="import_row",
            occurred_at=datetime(2026, 4, 23, 10 + index, 0, tzinfo=UTC),
            amount=Decimal(f"{100 + index}.00"),
            description=f"Transaction {index}",
        )

    response = client.get(
        f"{API_PREFIX}/transactions",
        params={"business_unit_id": str(test_business_unit.id), "limit": 2},
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 2
