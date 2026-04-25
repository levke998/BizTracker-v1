"""Integration tests for the MVP import flow."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.imports.infrastructure.orm.import_batch_model import ImportBatchModel
from app.modules.imports.infrastructure.orm.import_row_error_model import (
    ImportRowErrorModel,
)
from app.modules.imports.infrastructure.orm.import_row_model import ImportRowModel
from app.modules.master_data.infrastructure.orm.business_unit_model import (
    BusinessUnitModel,
)

API_PREFIX = "/api/v1/imports"


def test_list_import_batches_returns_uploaded_batch(
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
    assert upload_response.status_code == 201
    batch_id = upload_response.json()["id"]

    response = client.get(
        f"{API_PREFIX}/batches",
        params={"business_unit_id": str(test_business_unit.id)},
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["id"] == batch_id
    assert payload[0]["status"] == "uploaded"


def test_upload_creates_batch_and_file_metadata(
    client: TestClient,
    db_session: Session,
    imports_fixtures_dir: Path,
    test_business_unit: BusinessUnitModel,
    upload_import_fixture,
) -> None:
    response = upload_import_fixture(
        business_unit_id=test_business_unit.id,
        import_type="pos_sales",
        file_path=imports_fixtures_dir / "sample_pos_sales_clean.csv",
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "uploaded"
    assert payload["import_type"] == "pos_sales"
    assert payload["files"][0]["original_name"] == "sample_pos_sales_clean.csv"

    db_session.expire_all()
    stored_batch = db_session.scalar(
        select(ImportBatchModel).where(ImportBatchModel.id == UUID(payload["id"]))
    )
    assert stored_batch is not None
    assert stored_batch.business_unit_id == test_business_unit.id


def test_parse_succeeds_for_clean_csv(
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

    parse_response = client.post(f"{API_PREFIX}/batches/{batch_id}/parse")

    assert parse_response.status_code == 200
    payload = parse_response.json()
    assert payload["status"] == "parsed"
    assert payload["total_rows"] == 4
    assert payload["parsed_rows"] == 4
    assert payload["error_rows"] == 0

    db_session.expire_all()
    row_count = db_session.scalar(
        select(func.count()).select_from(ImportRowModel).where(
            ImportRowModel.batch_id == UUID(batch_id)
        )
    )
    assert row_count == 4

    first_row = db_session.scalar(
        select(ImportRowModel)
        .where(ImportRowModel.batch_id == UUID(batch_id))
        .order_by(ImportRowModel.row_number.asc())
    )
    assert first_row is not None
    assert first_row.normalized_payload == {
        "date": "2026-04-22",
        "receipt_no": "RCPT-1001",
        "category_name": None,
        "product_name": "Croissant",
        "quantity": 2,
        "gross_amount": 1200,
        "payment_method": "cash",
    }


def test_parse_bad_csv_creates_import_row_error(
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

    parse_response = client.post(f"{API_PREFIX}/batches/{batch_id}/parse")

    assert parse_response.status_code == 200
    payload = parse_response.json()
    assert payload["status"] == "parsed"
    assert payload["error_rows"] >= 1

    db_session.expire_all()
    error_count = db_session.scalar(
        select(func.count()).select_from(ImportRowErrorModel).where(
            ImportRowErrorModel.batch_id == UUID(batch_id)
        )
    )
    assert error_count >= 1


def test_parse_pos_sales_missing_required_column_returns_profile_error(
    client: TestClient,
    db_session: Session,
    imports_fixtures_dir: Path,
    test_business_unit: BusinessUnitModel,
    upload_import_fixture,
) -> None:
    upload_response = upload_import_fixture(
        business_unit_id=test_business_unit.id,
        import_type="pos_sales",
        file_path=imports_fixtures_dir / "sample_pos_sales_missing_required_column.csv",
    )
    batch_id = upload_response.json()["id"]

    parse_response = client.post(f"{API_PREFIX}/batches/{batch_id}/parse")

    assert parse_response.status_code == 200
    payload = parse_response.json()
    assert payload["status"] == "parsed"
    assert payload["total_rows"] == 0
    assert payload["parsed_rows"] == 0
    assert payload["error_rows"] == 1

    db_session.expire_all()
    stored_error = db_session.scalar(
        select(ImportRowErrorModel).where(ImportRowErrorModel.batch_id == UUID(batch_id))
    )
    assert stored_error is not None
    assert stored_error.error_code == "missing_required_columns"
    assert "gross_amount" in stored_error.message


def test_parse_pos_sales_normalizes_whitespace_and_empty_values(
    client: TestClient,
    db_session: Session,
    imports_fixtures_dir: Path,
    test_business_unit: BusinessUnitModel,
    upload_import_fixture,
) -> None:
    upload_response = upload_import_fixture(
        business_unit_id=test_business_unit.id,
        import_type="pos_sales",
        file_path=imports_fixtures_dir / "sample_pos_sales_whitespace_values.csv",
    )
    batch_id = upload_response.json()["id"]

    parse_response = client.post(f"{API_PREFIX}/batches/{batch_id}/parse")

    assert parse_response.status_code == 200
    payload = parse_response.json()
    assert payload["status"] == "parsed"
    assert payload["parsed_rows"] == 1

    db_session.expire_all()
    stored_row = db_session.scalar(
        select(ImportRowModel)
        .where(ImportRowModel.batch_id == UUID(batch_id))
        .order_by(ImportRowModel.row_number.asc())
    )
    assert stored_row is not None
    assert stored_row.normalized_payload == {
        "date": "2026-04-22",
        "receipt_no": None,
        "category_name": None,
        "product_name": "Latte Macchiato",
        "quantity": 2,
        "gross_amount": 1890,
        "payment_method": "card",
    }


def test_rows_endpoint_returns_staging_rows(
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
    client.post(f"{API_PREFIX}/batches/{batch_id}/parse")

    response = client.get(f"{API_PREFIX}/batches/{batch_id}/rows", params={"limit": 20})

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 4
    assert payload[0]["row_number"] == 2
    assert payload[0]["parse_status"] == "parsed"
    assert "date" in payload[0]["raw_payload"]


def test_errors_endpoint_returns_parse_errors(
    client: TestClient,
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
    client.post(f"{API_PREFIX}/batches/{batch_id}/parse")

    response = client.get(f"{API_PREFIX}/batches/{batch_id}/errors", params={"limit": 20})

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) >= 1
    assert payload[0]["error_code"] == "row_processing_error"
    assert "more columns than the csv header" in payload[0]["message"].lower()


def test_reparse_of_non_uploaded_batch_returns_conflict(
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

    first_parse_response = client.post(f"{API_PREFIX}/batches/{batch_id}/parse")
    assert first_parse_response.status_code == 200

    second_parse_response = client.post(f"{API_PREFIX}/batches/{batch_id}/parse")

    assert second_parse_response.status_code == 409
    assert "Only uploaded batches can be parsed." in second_parse_response.json()["detail"]
