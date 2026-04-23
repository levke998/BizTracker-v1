"""Integration tests for import-to-finance mapping."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.finance.infrastructure.orm.transaction_model import (
    FinancialTransactionModel,
)
from app.modules.master_data.infrastructure.orm.business_unit_model import (
    BusinessUnitModel,
)

IMPORTS_API_PREFIX = "/api/v1/imports"


def test_financial_transactions_are_created_from_clean_pos_sales_batch(
    client: TestClient,
    db_session: Session,
    imports_fixtures_dir: Path,
    test_business_unit: BusinessUnitModel,
    upload_import_fixture,
) -> None:
    upload_response = upload_import_fixture(
        business_unit_id=test_business_unit.id,
        import_type="pos_sales",
        file_path=imports_fixtures_dir / "sample_pos_sales_clean.csv",
    )
    batch_id = upload_response.json()["id"]
    client.post(f"{IMPORTS_API_PREFIX}/batches/{batch_id}/parse")

    mapping_response = client.post(
        f"{IMPORTS_API_PREFIX}/batches/{batch_id}/map/financial-transactions"
    )

    assert mapping_response.status_code == 200
    payload = mapping_response.json()
    assert payload["batch_id"] == batch_id
    assert payload["created_transactions"] == 4
    assert payload["transaction_type"] == "pos_sale"
    assert payload["source_type"] == "import_row"

    db_session.expire_all()
    stored_transactions = db_session.scalars(
        select(FinancialTransactionModel)
        .where(FinancialTransactionModel.business_unit_id == test_business_unit.id)
        .order_by(FinancialTransactionModel.occurred_at.asc())
    ).all()

    assert len(stored_transactions) == 4
    assert stored_transactions[0].direction == "inflow"
    assert stored_transactions[0].transaction_type == "pos_sale"
    assert stored_transactions[0].amount == Decimal("1200")
    assert stored_transactions[0].currency == "HUF"
    assert stored_transactions[0].description == "Croissant (RCPT-1001)"
    assert stored_transactions[0].source_type == "import_row"


def test_only_parsed_rows_are_mapped_to_financial_transactions(
    client: TestClient,
    db_session: Session,
    imports_fixtures_dir: Path,
    test_business_unit: BusinessUnitModel,
    upload_import_fixture,
) -> None:
    upload_response = upload_import_fixture(
        business_unit_id=test_business_unit.id,
        import_type="pos_sales",
        file_path=imports_fixtures_dir / "sample_pos_sales_with_issues.csv",
    )
    batch_id = upload_response.json()["id"]
    parse_response = client.post(f"{IMPORTS_API_PREFIX}/batches/{batch_id}/parse")
    assert parse_response.status_code == 200
    assert parse_response.json()["parsed_rows"] == 2

    mapping_response = client.post(
        f"{IMPORTS_API_PREFIX}/batches/{batch_id}/map/financial-transactions"
    )

    assert mapping_response.status_code == 200
    assert mapping_response.json()["created_transactions"] == 2

    db_session.expire_all()
    count = db_session.scalar(
        select(func.count())
        .select_from(FinancialTransactionModel)
        .where(FinancialTransactionModel.business_unit_id == test_business_unit.id)
    )
    assert count == 2


def test_mapping_rejects_batch_that_is_not_parsed(
    client: TestClient,
    imports_fixtures_dir: Path,
    test_business_unit: BusinessUnitModel,
    upload_import_fixture,
) -> None:
    upload_response = upload_import_fixture(
        business_unit_id=test_business_unit.id,
        import_type="pos_sales",
        file_path=imports_fixtures_dir / "sample_pos_sales_clean.csv",
    )
    batch_id = upload_response.json()["id"]

    mapping_response = client.post(
        f"{IMPORTS_API_PREFIX}/batches/{batch_id}/map/financial-transactions"
    )

    assert mapping_response.status_code == 409
    assert "Only parsed batches can be mapped" in mapping_response.json()["detail"]


def test_same_batch_cannot_be_mapped_twice(
    client: TestClient,
    imports_fixtures_dir: Path,
    test_business_unit: BusinessUnitModel,
    upload_import_fixture,
) -> None:
    upload_response = upload_import_fixture(
        business_unit_id=test_business_unit.id,
        import_type="pos_sales",
        file_path=imports_fixtures_dir / "sample_pos_sales_clean.csv",
    )
    batch_id = upload_response.json()["id"]
    client.post(f"{IMPORTS_API_PREFIX}/batches/{batch_id}/parse")

    first_mapping_response = client.post(
        f"{IMPORTS_API_PREFIX}/batches/{batch_id}/map/financial-transactions"
    )
    assert first_mapping_response.status_code == 200

    second_mapping_response = client.post(
        f"{IMPORTS_API_PREFIX}/batches/{batch_id}/map/financial-transactions"
    )

    assert second_mapping_response.status_code == 409
    assert "already been mapped" in second_mapping_response.json()["detail"]
