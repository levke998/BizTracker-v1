"""Integration tests for the demo POS API."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.modules.finance.infrastructure.orm.transaction_model import (
    FinancialTransactionModel,
)
from app.modules.imports.infrastructure.orm.import_batch_model import ImportBatchModel
from app.modules.imports.infrastructure.orm.import_row_model import ImportRowModel
from app.modules.master_data.infrastructure.orm.business_unit_model import (
    BusinessUnitModel,
)
from app.modules.master_data.infrastructure.orm.category_model import CategoryModel
from app.modules.master_data.infrastructure.orm.product_model import ProductModel

API_PREFIX = "/api/v1/demo-pos"


def test_demo_pos_creates_import_rows_and_finance_transactions(
    client: TestClient,
    db_session: Session,
    test_business_unit: BusinessUnitModel,
) -> None:
    category = CategoryModel(
        business_unit_id=test_business_unit.id,
        name="Demo POS Category",
        is_active=True,
    )
    db_session.add(category)
    db_session.flush()
    product = ProductModel(
        business_unit_id=test_business_unit.id,
        category_id=category.id,
        sku="TEST-POS-001",
        name="Demo POS Latte",
        product_type="beverage",
        sale_price_gross=Decimal("750"),
        default_unit_cost=Decimal("210"),
        currency="HUF",
        is_active=True,
    )
    db_session.add(product)
    db_session.commit()

    receipt_no = "TEST-DEMO-POS-001"
    try:
        response = client.post(
            f"{API_PREFIX}/receipts",
            json={
                "business_unit_id": str(test_business_unit.id),
                "receipt_no": receipt_no,
                "payment_method": "card",
                "occurred_at": "2026-04-24T14:20:00+02:00",
                "lines": [
                    {
                        "product_id": str(product.id),
                        "quantity": 2,
                    }
                ],
            },
        )

        assert response.status_code == 201
        payload = response.json()
        assert payload["receipt_no"] == receipt_no
        assert payload["gross_total"] == "1500.00"
        assert payload["transaction_count"] == 1
        assert payload["lines"][0]["product_name"] == "Demo POS Latte"
        assert payload["lines"][0]["category_name"] == "Demo POS Category"

        batch_id = UUID(payload["batch_id"])
        db_session.expire_all()
        batch = db_session.get(ImportBatchModel, batch_id)
        assert batch is not None
        assert batch.import_type == "pos_sales"
        assert batch.status == "parsed"

        row = db_session.scalar(
            select(ImportRowModel).where(ImportRowModel.batch_id == batch_id)
        )
        assert row is not None
        assert row.normalized_payload["receipt_no"] == receipt_no
        assert row.normalized_payload["gross_amount"] == 1500

        transaction = db_session.scalar(
            select(FinancialTransactionModel).where(
                FinancialTransactionModel.source_id == row.id
            )
        )
        assert transaction is not None
        assert transaction.amount == Decimal("1500.00")
        assert transaction.transaction_type == "pos_sale"
    finally:
        row_ids = [
            row_id
            for row_id, in db_session.execute(
                select(ImportRowModel.id)
                .join(ImportBatchModel, ImportRowModel.batch_id == ImportBatchModel.id)
                .where(ImportBatchModel.business_unit_id == test_business_unit.id)
            ).all()
        ]
        if row_ids:
            db_session.execute(
                delete(FinancialTransactionModel).where(
                    FinancialTransactionModel.source_id.in_(row_ids)
                )
            )
        db_session.execute(
            delete(ImportBatchModel).where(
                ImportBatchModel.business_unit_id == test_business_unit.id
            )
        )
        db_session.execute(delete(ProductModel).where(ProductModel.id == product.id))
        db_session.execute(delete(CategoryModel).where(CategoryModel.id == category.id))
        db_session.commit()
