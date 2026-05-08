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
from app.modules.master_data.infrastructure.orm.category_model import CategoryModel
from app.modules.master_data.infrastructure.orm.business_unit_model import (
    BusinessUnitModel,
)
from app.modules.master_data.infrastructure.orm.product_model import ProductModel
from app.modules.pos_ingestion.infrastructure.orm.pos_product_alias_model import (
    PosProductAliasModel,
)
from app.modules.production.infrastructure.orm.recipe_model import RecipeModel

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
    assert payload["first_occurred_at"] == "2026-04-22"
    assert payload["last_occurred_at"] == "2026-04-22"

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
        "product_id": None,
        "sku": None,
        "category_name": None,
        "product_name": "Croissant",
        "quantity": 2,
        "gross_amount": 1200,
        "payment_method": "cash",
    }

    aliases = db_session.scalars(
        select(PosProductAliasModel)
        .where(PosProductAliasModel.business_unit_id == test_business_unit.id)
        .order_by(PosProductAliasModel.source_product_name.asc())
    ).all()
    assert len(aliases) == 4
    croissant_alias = next(
        alias for alias in aliases if alias.source_product_name == "Croissant"
    )
    assert croissant_alias.source_system == "pos_sales"
    assert croissant_alias.source_product_key == "name:croissant"
    assert croissant_alias.status == "auto_created"
    assert croissant_alias.mapping_confidence == "name_auto"
    assert croissant_alias.occurrence_count == 1
    assert croissant_alias.product_id is not None

    alias_response = client.get(
        "/api/v1/pos-ingestion/product-aliases",
        params={"business_unit_id": str(test_business_unit.id), "status": "auto_created"},
    )
    assert alias_response.status_code == 200
    alias_payload = alias_response.json()
    assert len(alias_payload) == 4
    assert alias_payload[0]["source_system"] == "pos_sales"
    assert alias_payload[0]["status"] == "auto_created"


def test_parse_pos_sales_coalesces_repeated_product_aliases_in_same_batch(
    client: TestClient,
    db_session: Session,
    tmp_path: Path,
    test_business_unit: BusinessUnitModel,
    upload_import_fixture,
) -> None:
    file_path = tmp_path / "repeated_product.csv"
    file_path.write_text(
        "\n".join(
            [
                "Date,Receipt No,Product Name,Quantity,Gross Amount,Payment Method",
                "2026-05-01,RCPT-1,Vegyes sos,1,500,cash",
                "2026-05-01,RCPT-2,Vegyes sos,2,1000,cash",
                "2026-05-02,RCPT-3,Vegyes sos,1,600,cash",
            ]
        ),
        encoding="utf-8",
    )
    upload_response = upload_import_fixture(
        business_unit_id=test_business_unit.id,
        import_type="pos_sales",
        file_path=file_path,
    )
    assert upload_response.status_code == 201
    batch_id = upload_response.json()["id"]

    parse_response = client.post(f"{API_PREFIX}/batches/{batch_id}/parse")

    assert parse_response.status_code == 200
    payload = parse_response.json()
    assert payload["status"] == "parsed"
    assert payload["total_rows"] == 3
    assert payload["parsed_rows"] == 3
    assert payload["error_rows"] == 0

    db_session.expire_all()
    aliases = db_session.scalars(
        select(PosProductAliasModel).where(
            PosProductAliasModel.business_unit_id == test_business_unit.id,
            PosProductAliasModel.source_system == "pos_sales",
            PosProductAliasModel.source_product_key == "name:vegyes sos",
        )
    ).all()
    assert len(aliases) == 1
    assert aliases[0].occurrence_count == 3

    product_count = db_session.scalar(
        select(func.count()).select_from(ProductModel).where(
            ProductModel.business_unit_id == test_business_unit.id,
            ProductModel.name == "Vegyes sos",
        )
    )
    assert product_count == 1


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


def test_pos_product_alias_can_be_approved_and_stays_mapped_on_reimport(
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

    db_session.expire_all()
    alias = db_session.scalar(
        select(PosProductAliasModel).where(
            PosProductAliasModel.business_unit_id == test_business_unit.id,
            PosProductAliasModel.source_product_key == "name:croissant",
        )
    )
    assert alias is not None
    assert alias.status == "auto_created"

    approved_product = ProductModel(
        business_unit_id=test_business_unit.id,
        category_id=None,
        sales_uom_id=None,
        sku="APPROVED-CROISSANT",
        name="Approved Croissant",
        product_type="finished_good",
        sale_price_gross=None,
        default_unit_cost=None,
        currency="HUF",
        is_active=True,
    )
    db_session.add(approved_product)
    db_session.commit()
    db_session.refresh(approved_product)

    approval_response = client.patch(
        f"/api/v1/pos-ingestion/product-aliases/{alias.id}/mapping",
        json={
            "product_id": str(approved_product.id),
            "notes": "Manual POS review",
        },
    )

    assert approval_response.status_code == 200
    approval_payload = approval_response.json()
    assert approval_payload["product_id"] == str(approved_product.id)
    assert approval_payload["status"] == "mapped"
    assert approval_payload["mapping_confidence"] == "manual"

    second_upload_response = upload_import_fixture(
        business_unit_id=test_business_unit.id,
        import_type="pos_sales",
        file_path=imports_fixtures_dir / "sample_pos_sales_clean.csv",
    )
    second_batch_id = second_upload_response.json()["id"]
    second_parse_response = client.post(f"{API_PREFIX}/batches/{second_batch_id}/parse")
    assert second_parse_response.status_code == 200

    db_session.expire_all()
    mapped_alias = db_session.get(PosProductAliasModel, alias.id)
    assert mapped_alias is not None
    assert mapped_alias.product_id == approved_product.id
    assert mapped_alias.status == "mapped"
    assert mapped_alias.mapping_confidence == "manual"
    assert mapped_alias.occurrence_count == 2


def test_pos_catalog_sale_price_uses_latest_sale_date_not_import_order(
    client: TestClient,
    db_session: Session,
    tmp_path: Path,
    test_business_unit: BusinessUnitModel,
    upload_import_fixture,
) -> None:
    newer_file = tmp_path / "newer_price.csv"
    newer_file.write_text(
        "\n".join(
            [
                "Date,Receipt No,Product Name,Quantity,Gross Amount,Payment Method",
                "2026-05-02,RCPT-NEW,Adaptive Cake,1,150,cash",
            ]
        ),
        encoding="utf-8",
    )
    older_file = tmp_path / "older_price.csv"
    older_file.write_text(
        "\n".join(
            [
                "Date,Receipt No,Product Name,Quantity,Gross Amount,Payment Method",
                "2026-05-01,RCPT-OLD,Adaptive Cake,1,100,cash",
            ]
        ),
        encoding="utf-8",
    )

    newer_upload = upload_import_fixture(
        business_unit_id=test_business_unit.id,
        import_type="pos_sales",
        file_path=newer_file,
    )
    assert newer_upload.status_code == 201
    newer_parse = client.post(f"{API_PREFIX}/batches/{newer_upload.json()['id']}/parse")
    assert newer_parse.status_code == 200

    older_upload = upload_import_fixture(
        business_unit_id=test_business_unit.id,
        import_type="pos_sales",
        file_path=older_file,
    )
    assert older_upload.status_code == 201
    older_parse = client.post(f"{API_PREFIX}/batches/{older_upload.json()['id']}/parse")
    assert older_parse.status_code == 200

    db_session.expire_all()
    product = db_session.scalar(
        select(ProductModel).where(
            ProductModel.business_unit_id == test_business_unit.id,
            ProductModel.name == "Adaptive Cake",
        )
    )
    assert product is not None
    assert product.sale_price_gross == 150
    assert product.sale_price_source == "pos_sales"
    assert product.sale_price_last_seen_at is not None
    assert product.sale_price_last_seen_at.date().isoformat() == "2026-05-02"


def test_pos_missing_recipe_worklist_returns_pos_products_without_active_recipe(
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
    assert upload_response.status_code == 201
    batch_id = upload_response.json()["id"]
    parse_response = client.post(f"{API_PREFIX}/batches/{batch_id}/parse")
    assert parse_response.status_code == 200

    response = client.get(
        "/api/v1/pos-ingestion/products/missing-recipes",
        params={"business_unit_id": str(test_business_unit.id)},
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 4
    assert {item["product_name"] for item in payload} == {
        "Bagel",
        "Croissant",
        "Espresso",
        "Macaron Box",
    }
    croissant = next(item for item in payload if item["product_name"] == "Croissant")
    assert croissant["occurrence_count"] == 1
    assert croissant["latest_source_system"] == "pos_sales"
    assert croissant["sale_price_gross"] == "600.00"

    db_session.expire_all()
    croissant_product = db_session.scalar(
        select(ProductModel).where(
            ProductModel.business_unit_id == test_business_unit.id,
            ProductModel.name == "Croissant",
        )
    )
    assert croissant_product is not None
    db_session.add(
        RecipeModel(
            product_id=croissant_product.id,
            name="Croissant recipe",
            is_active=True,
        )
    )
    db_session.commit()

    refreshed_response = client.get(
        "/api/v1/pos-ingestion/products/missing-recipes",
        params={"business_unit_id": str(test_business_unit.id)},
    )

    assert refreshed_response.status_code == 200
    refreshed_payload = refreshed_response.json()
    assert len(refreshed_payload) == 3
    assert "Croissant" not in {
        item["product_name"] for item in refreshed_payload
    }


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
        "product_id": None,
        "sku": None,
        "category_name": None,
        "product_name": "Latte Macchiato",
        "quantity": 2,
        "gross_amount": 1890,
        "payment_method": "card",
    }


def test_parse_gourmand_pos_sales_file_set_uses_summary_categories(
    client: TestClient,
    db_session: Session,
    imports_fixtures_dir: Path,
    test_business_unit: BusinessUnitModel,
) -> None:
    files = []
    file_objects = []
    for fixture_name in (
        "gourmand_summary_0412_0427.csv",
        "gourmand_detail_0412_0419.csv",
        "gourmand_detail_0420_0427.csv",
    ):
        file_path = imports_fixtures_dir / fixture_name
        file_object = file_path.open("rb")
        file_objects.append(file_object)
        files.append(("files", (file_path.name, file_object, "text/csv")))

    try:
        upload_response = client.post(
            f"{API_PREFIX}/file-set",
            data={
                "business_unit_id": str(test_business_unit.id),
                "import_type": "gourmand_pos_sales",
            },
            files=files,
        )
    finally:
        for file_object in file_objects:
            file_object.close()

    assert upload_response.status_code == 201
    batch_id = upload_response.json()["id"]
    assert len(upload_response.json()["files"]) == 3

    parse_response = client.post(f"{API_PREFIX}/batches/{batch_id}/parse")

    assert parse_response.status_code == 200
    payload = parse_response.json()
    assert payload["status"] == "parsed"
    assert payload["total_rows"] == 4
    assert payload["parsed_rows"] == 4
    assert payload["error_rows"] == 0
    assert payload["first_occurred_at"] == "2026-04-12T10:07:00+02:00"
    assert payload["last_occurred_at"] == "2026-04-20T11:22:00+02:00"

    db_session.expire_all()
    rows = db_session.scalars(
        select(ImportRowModel)
        .where(ImportRowModel.batch_id == UUID(batch_id))
        .order_by(ImportRowModel.row_number.asc(), ImportRowModel.created_at.asc())
    ).all()

    assert len(rows) == 4
    first_payload = rows[0].normalized_payload
    assert first_payload is not None
    assert first_payload["product_name"] == "Fagylalt"
    assert first_payload["category_name"] == "Fagylalt"
    assert first_payload["date"] == "2026-04-12"
    assert first_payload["occurred_at"] == "2026-04-12T10:07:00+02:00"
    assert first_payload["receipt_no"] == "GOURMAND-20260412-1007-gourmandcuki"
    assert first_payload["source_import_profile"] == "gourmand_pos_sales"
    assert first_payload["source_line_key"]

    discounted_payloads = [
        row.normalized_payload
        for row in rows
        if row.normalized_payload
        and row.normalized_payload["product_name"] == "Kis torta doboz"
    ]
    assert discounted_payloads[0]["category_name"] == "Csomagolás"
    assert discounted_payloads[0]["discount_note"] == "-20 %"

    category = db_session.scalar(
        select(CategoryModel).where(
            CategoryModel.business_unit_id == test_business_unit.id,
            CategoryModel.name == "Fagylalt",
        )
    )
    assert category is not None

    product = db_session.scalar(
        select(ProductModel).where(
            ProductModel.business_unit_id == test_business_unit.id,
            ProductModel.name == "Fagylalt",
        )
    )
    assert product is not None
    assert product.category_id == category.id
    assert product.sale_price_gross == 600


def test_parse_gourmand_pos_sales_blocks_mismatched_metadata_periods(
    client: TestClient,
    tmp_path: Path,
    test_business_unit: BusinessUnitModel,
) -> None:
    summary_file = tmp_path / "osszesites_0427_0501.csv"
    summary_file.write_text(
        "\n".join(
            [
                "NAPI ÖSSZESSÍTÉS",
                "Gourmand Cukrászda",
                "Lekérdezve: 2026. 05. 01. 18:55",
                "Adatok: 2026.04.27. - 2026.05.01.",
                "",
                "NÉV;KATEGÓRIA;ÁR;MENNYISÉG;Fizetve;ÖSSZESEN",
                " Fagylalt;Fagylalt;600 Ft;1;Igen;600 Ft",
            ]
        ),
        encoding="utf-8",
    )
    detail_file = tmp_path / "teteles_0427_0430.csv"
    detail_file.write_text(
        "\n".join(
            [
                "TÉTELES RENDELÉSEK",
                "Gourmand Cukrászda",
                "Lekérdezve: 2026. 05. 01. 18:53",
                "Adatok: 2026.04.27. - 2026.04.30.",
                "",
                "DÁTUM;FELHASZNÁLÓ;NÉV;ÁR;MENNYISÉG;ÖSSZESEN",
                "2026.04.27. 11:40;gourmandcuki; Fagylalt;600 Ft;1;600 Ft",
            ]
        ),
        encoding="utf-8",
    )

    file_objects = [summary_file.open("rb"), detail_file.open("rb")]
    files = [
        ("files", (summary_file.name, file_objects[0], "text/csv")),
        ("files", (detail_file.name, file_objects[1], "text/csv")),
    ]

    try:
        upload_response = client.post(
            f"{API_PREFIX}/file-set",
            data={
                "business_unit_id": str(test_business_unit.id),
                "import_type": "gourmand_pos_sales",
            },
            files=files,
        )
    finally:
        for file_object in file_objects:
            file_object.close()

    assert upload_response.status_code == 201
    batch_id = upload_response.json()["id"]

    parse_response = client.post(f"{API_PREFIX}/batches/{batch_id}/parse")

    assert parse_response.status_code == 200
    payload = parse_response.json()
    assert payload["status"] == "parsed"
    assert payload["total_rows"] == 0
    assert payload["parsed_rows"] == 0
    assert payload["error_rows"] == 1

    errors_response = client.get(f"{API_PREFIX}/batches/{batch_id}/errors")
    assert errors_response.status_code == 200
    errors = errors_response.json()
    assert errors[0]["error_code"] == "pos_period_mismatch"
    assert errors[0]["raw_payload"]["summary_period"] == {
        "start": "2026-04-27",
        "end": "2026-05-01",
    }
    assert errors[0]["raw_payload"]["detail_combined_period"] == {
        "start": "2026-04-27",
        "end": "2026-04-30",
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
