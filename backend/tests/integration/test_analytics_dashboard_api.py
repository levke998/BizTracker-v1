"""Integration tests for the business dashboard read APIs."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.modules.finance.infrastructure.orm.transaction_model import (
    FinancialTransactionModel,
)
from app.modules.imports.infrastructure.orm.import_batch_model import ImportBatchModel
from app.modules.imports.infrastructure.orm.import_file_model import ImportFileModel
from app.modules.imports.infrastructure.orm.import_row_model import ImportRowModel
from app.modules.master_data.infrastructure.orm.business_unit_model import (
    BusinessUnitModel,
)

API_PREFIX = "/api/v1/analytics"


@dataclass
class AnalyticsTestDataBuilder:
    """Create dashboard source records and clean only those records afterwards."""

    db_session: Session
    transaction_ids: list = field(default_factory=list)
    batch_ids: list = field(default_factory=list)
    file_ids: list = field(default_factory=list)
    row_ids: list = field(default_factory=list)

    def create_transaction(
        self,
        *,
        business_unit_id,
        direction: str,
        transaction_type: str,
        amount: Decimal,
        occurred_at: datetime,
        description: str,
        source_type: str,
    ) -> FinancialTransactionModel:
        transaction = FinancialTransactionModel(
            business_unit_id=business_unit_id,
            direction=direction,
            transaction_type=transaction_type,
            amount=amount,
            currency="HUF",
            occurred_at=occurred_at,
            description=description,
            source_type=source_type,
            source_id=uuid4(),
        )
        self.db_session.add(transaction)
        self.db_session.commit()
        self.db_session.refresh(transaction)
        self.transaction_ids.append(transaction.id)
        return transaction

    def create_pos_row(
        self,
        *,
        business_unit_id,
        row_number: int,
        payload_date: date,
        receipt_no: str,
        category_name: str,
        product_name: str,
        quantity: Decimal,
        gross_amount: Decimal,
    ) -> ImportRowModel:
        batch = ImportBatchModel(
            business_unit_id=business_unit_id,
            import_type="pos_sales",
            status="parsed",
            started_at=datetime.now(UTC),
            finished_at=datetime.now(UTC),
            total_rows=1,
            parsed_rows=1,
            error_rows=0,
        )
        self.db_session.add(batch)
        self.db_session.flush()

        import_file = ImportFileModel(
            batch_id=batch.id,
            original_name=f"analytics-test-{uuid4().hex[:8]}.csv",
            stored_path=f"storage/imports/analytics-test-{uuid4().hex}.csv",
            mime_type="text/csv",
            size_bytes=128,
        )
        self.db_session.add(import_file)
        self.db_session.flush()

        row = ImportRowModel(
            batch_id=batch.id,
            file_id=import_file.id,
            row_number=row_number,
            raw_payload={
                "date": payload_date.isoformat(),
                "receipt_no": receipt_no,
                "category_name": category_name,
                "product_name": product_name,
                "quantity": str(quantity),
                "gross_amount": str(gross_amount),
                "payment_method": "cash",
            },
            normalized_payload={
                "date": payload_date.isoformat(),
                "receipt_no": receipt_no,
                "category_name": category_name,
                "product_name": product_name,
                "quantity": str(quantity),
                "gross_amount": str(gross_amount),
                "payment_method": "cash",
            },
            parse_status="parsed",
        )
        self.db_session.add(row)
        self.db_session.commit()
        self.db_session.refresh(row)

        self.batch_ids.append(batch.id)
        self.file_ids.append(import_file.id)
        self.row_ids.append(row.id)
        return row

    def cleanup(self) -> None:
        self.db_session.rollback()
        if self.transaction_ids:
            self.db_session.execute(
                delete(FinancialTransactionModel).where(
                    FinancialTransactionModel.id.in_(self.transaction_ids)
                )
            )
        if self.row_ids:
            self.db_session.execute(
                delete(ImportRowModel).where(ImportRowModel.id.in_(self.row_ids))
            )
        if self.file_ids:
            self.db_session.execute(
                delete(ImportFileModel).where(ImportFileModel.id.in_(self.file_ids))
            )
        if self.batch_ids:
            self.db_session.execute(
                delete(ImportBatchModel).where(ImportBatchModel.id.in_(self.batch_ids))
            )
        self.db_session.commit()


@pytest.fixture
def analytics_data_builder(db_session: Session):
    """Yield a dashboard test data builder with explicit cleanup."""

    builder = AnalyticsTestDataBuilder(db_session=db_session)
    try:
        yield builder
    finally:
        builder.cleanup()


@pytest.fixture
def flow_business_unit(db_session: Session) -> BusinessUnitModel:
    """Return the seeded Flow business unit."""

    business_unit = db_session.scalar(
        select(BusinessUnitModel).where(BusinessUnitModel.code == "flow")
    )
    if business_unit is None:
        raise RuntimeError("Expected seeded 'flow' business unit to exist.")
    return business_unit


def _kpi_value(payload: dict, code: str) -> Decimal:
    for kpi in payload["kpis"]:
        if kpi["code"] == code:
            return Decimal(str(kpi["value"]))
    raise AssertionError(f"Missing dashboard KPI: {code}")


def test_dashboard_returns_kpis_and_breakdowns_for_business_unit(
    client: TestClient,
    analytics_data_builder: AnalyticsTestDataBuilder,
    test_business_unit: BusinessUnitModel,
) -> None:
    business_date = date(2030, 1, 10)
    analytics_data_builder.create_transaction(
        business_unit_id=test_business_unit.id,
        direction="inflow",
        transaction_type="pos_sale",
        amount=Decimal("1000.00"),
        occurred_at=datetime(2030, 1, 10, 10, 0, tzinfo=UTC),
        description="Dashboard test revenue",
        source_type="analytics_test_revenue",
    )
    analytics_data_builder.create_transaction(
        business_unit_id=test_business_unit.id,
        direction="outflow",
        transaction_type="supplier_invoice",
        amount=Decimal("250.00"),
        occurred_at=datetime(2030, 1, 10, 12, 0, tzinfo=UTC),
        description="Dashboard test cost",
        source_type="analytics_test_cost",
    )
    analytics_data_builder.create_pos_row(
        business_unit_id=test_business_unit.id,
        row_number=2,
        payload_date=business_date,
        receipt_no="DASH-1001",
        category_name="Pastry",
        product_name="Croissant",
        quantity=Decimal("2"),
        gross_amount=Decimal("1000"),
    )

    response = client.get(
        f"{API_PREFIX}/dashboard",
        params={
            "scope": "overall",
            "business_unit_id": str(test_business_unit.id),
            "period": "custom",
            "start_date": "2030-01-01",
            "end_date": "2030-01-31",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["scope"] == "overall"
    assert payload["business_unit_id"] == str(test_business_unit.id)
    assert _kpi_value(payload, "revenue") == Decimal("1000.00")
    assert _kpi_value(payload, "cost") == Decimal("250.00")
    assert _kpi_value(payload, "profit") == Decimal("750.00")
    assert _kpi_value(payload, "estimated_cogs") == Decimal("0")
    assert _kpi_value(payload, "transaction_count") == Decimal("2")
    assert _kpi_value(payload, "profit_margin") == Decimal("1000.00")
    assert _kpi_value(payload, "gross_margin_percent") == Decimal("100.00")
    assert _kpi_value(payload, "average_basket_value") == Decimal("1000")
    assert _kpi_value(payload, "average_basket_quantity") == Decimal("2")
    assert payload["category_breakdown"][0]["label"] == "Pastry"
    assert Decimal(str(payload["category_breakdown"][0]["revenue"])) == Decimal("1000")
    assert payload["top_products"][0]["label"] == "Croissant"
    assert payload["expense_breakdown"][0]["label"] == "supplier_invoice"


def test_dashboard_scope_filters_overall_flow_and_gourmand(
    client: TestClient,
    analytics_data_builder: AnalyticsTestDataBuilder,
    flow_business_unit: BusinessUnitModel,
    gourmand_business_unit: BusinessUnitModel,
) -> None:
    analytics_data_builder.create_transaction(
        business_unit_id=flow_business_unit.id,
        direction="inflow",
        transaction_type="pos_sale",
        amount=Decimal("110.00"),
        occurred_at=datetime(2031, 2, 3, 10, 0, tzinfo=UTC),
        description="Flow dashboard revenue",
        source_type="analytics_test_scope_flow",
    )
    analytics_data_builder.create_transaction(
        business_unit_id=gourmand_business_unit.id,
        direction="inflow",
        transaction_type="pos_sale",
        amount=Decimal("220.00"),
        occurred_at=datetime(2031, 2, 3, 10, 0, tzinfo=UTC),
        description="Gourmand dashboard revenue",
        source_type="analytics_test_scope_gourmand",
    )

    params = {
        "period": "custom",
        "start_date": "2031-02-01",
        "end_date": "2031-02-28",
    }
    overall_response = client.get(
        f"{API_PREFIX}/dashboard",
        params={**params, "scope": "overall"},
    )
    flow_response = client.get(
        f"{API_PREFIX}/dashboard",
        params={**params, "scope": "flow"},
    )
    gourmand_response = client.get(
        f"{API_PREFIX}/dashboard",
        params={**params, "scope": "gourmand"},
    )

    assert overall_response.status_code == 200
    assert flow_response.status_code == 200
    assert gourmand_response.status_code == 200
    assert _kpi_value(overall_response.json(), "revenue") == Decimal("330.00")
    assert _kpi_value(flow_response.json(), "revenue") == Decimal("110.00")
    assert flow_response.json()["business_unit_id"] == str(flow_business_unit.id)
    assert _kpi_value(gourmand_response.json(), "revenue") == Decimal("220.00")
    assert gourmand_response.json()["business_unit_id"] == str(gourmand_business_unit.id)


def test_dashboard_period_presets_resolve_year_and_last_30_days(
    client: TestClient,
    analytics_data_builder: AnalyticsTestDataBuilder,
    test_business_unit: BusinessUnitModel,
) -> None:
    today = datetime.now(UTC).date()
    analytics_data_builder.create_transaction(
        business_unit_id=test_business_unit.id,
        direction="inflow",
        transaction_type="pos_sale",
        amount=Decimal("123.00"),
        occurred_at=datetime.combine(today, datetime.min.time(), tzinfo=UTC),
        description="Current period revenue",
        source_type="analytics_test_period",
    )

    year_response = client.get(
        f"{API_PREFIX}/dashboard",
        params={
            "scope": "overall",
            "business_unit_id": str(test_business_unit.id),
            "period": "year",
        },
    )
    last_30_days_response = client.get(
        f"{API_PREFIX}/dashboard",
        params={
            "scope": "overall",
            "business_unit_id": str(test_business_unit.id),
            "period": "last_30_days",
        },
    )

    assert year_response.status_code == 200
    assert year_response.json()["period"]["grain"] == "month"
    assert _kpi_value(year_response.json(), "revenue") == Decimal("123.00")
    assert last_30_days_response.status_code == 200
    assert last_30_days_response.json()["period"]["grain"] == "day"
    assert _kpi_value(last_30_days_response.json(), "revenue") == Decimal("123.00")


def test_dashboard_category_and_product_drill_down_use_import_rows(
    client: TestClient,
    analytics_data_builder: AnalyticsTestDataBuilder,
    test_business_unit: BusinessUnitModel,
) -> None:
    analytics_data_builder.create_pos_row(
        business_unit_id=test_business_unit.id,
        row_number=2,
        payload_date=date(2032, 3, 4),
        receipt_no="DASH-2001",
        category_name="Pastry",
        product_name="Croissant",
        quantity=Decimal("2"),
        gross_amount=Decimal("1200"),
    )
    analytics_data_builder.create_pos_row(
        business_unit_id=test_business_unit.id,
        row_number=3,
        payload_date=date(2032, 3, 4),
        receipt_no="DASH-2002",
        category_name="Coffee",
        product_name="Espresso",
        quantity=Decimal("1"),
        gross_amount=Decimal("750"),
    )

    common_params = {
        "scope": "overall",
        "business_unit_id": str(test_business_unit.id),
        "period": "custom",
        "start_date": "2032-03-01",
        "end_date": "2032-03-31",
    }
    categories_response = client.get(
        f"{API_PREFIX}/dashboard/categories",
        params=common_params,
    )
    products_response = client.get(
        f"{API_PREFIX}/dashboard/products",
        params={**common_params, "category_name": "Pastry"},
    )

    assert categories_response.status_code == 200
    categories = categories_response.json()
    assert [row["label"] for row in categories] == ["Pastry", "Coffee"]
    assert categories[0]["source_layer"] == "import_derived"

    assert products_response.status_code == 200
    products = products_response.json()
    assert len(products) == 1
    assert products[0]["product_name"] == "Croissant"
    assert products[0]["category_name"] == "Pastry"
    assert Decimal(str(products[0]["revenue"])) == Decimal("1200")
    assert products[0]["source_layer"] == "import_derived"


def test_dashboard_product_source_rows_return_pos_import_rows(
    client: TestClient,
    analytics_data_builder: AnalyticsTestDataBuilder,
    test_business_unit: BusinessUnitModel,
) -> None:
    source_row = analytics_data_builder.create_pos_row(
        business_unit_id=test_business_unit.id,
        row_number=7,
        payload_date=date(2032, 5, 6),
        receipt_no="DASH-2501",
        category_name="Pastry",
        product_name="Croissant",
        quantity=Decimal("3"),
        gross_amount=Decimal("1800"),
    )
    analytics_data_builder.create_pos_row(
        business_unit_id=test_business_unit.id,
        row_number=8,
        payload_date=date(2032, 5, 6),
        receipt_no="DASH-2502",
        category_name="Coffee",
        product_name="Espresso",
        quantity=Decimal("1"),
        gross_amount=Decimal("750"),
    )

    response = client.get(
        f"{API_PREFIX}/dashboard/product-rows",
        params={
            "scope": "overall",
            "business_unit_id": str(test_business_unit.id),
            "period": "custom",
            "start_date": "2032-05-01",
            "end_date": "2032-05-31",
            "category_name": "Pastry",
            "product_name": "Croissant",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["row_id"] == str(source_row.id)
    assert payload[0]["row_number"] == 7
    assert payload[0]["date"] == "2032-05-06"
    assert payload[0]["receipt_no"] == "DASH-2501"
    assert payload[0]["category_name"] == "Pastry"
    assert payload[0]["product_name"] == "Croissant"
    assert Decimal(str(payload[0]["quantity"])) == Decimal("3")
    assert Decimal(str(payload[0]["gross_amount"])) == Decimal("1800")
    assert payload[0]["source_layer"] == "import_derived"


def test_dashboard_expense_drill_down_returns_financial_actual_rows(
    client: TestClient,
    analytics_data_builder: AnalyticsTestDataBuilder,
    test_business_unit: BusinessUnitModel,
) -> None:
    expense_transaction = analytics_data_builder.create_transaction(
        business_unit_id=test_business_unit.id,
        direction="outflow",
        transaction_type="supplier_invoice",
        amount=Decimal("4500.00"),
        occurred_at=datetime(2033, 4, 5, 9, 0, tzinfo=UTC),
        description="Supplier invoice DASH-3001",
        source_type="supplier_invoice",
    )
    analytics_data_builder.create_transaction(
        business_unit_id=test_business_unit.id,
        direction="inflow",
        transaction_type="pos_sale",
        amount=Decimal("9000.00"),
        occurred_at=datetime(2033, 4, 5, 10, 0, tzinfo=UTC),
        description="Revenue control row",
        source_type="analytics_test_revenue_control",
    )

    response = client.get(
        f"{API_PREFIX}/dashboard/expenses",
        params={
            "scope": "overall",
            "business_unit_id": str(test_business_unit.id),
            "period": "custom",
            "start_date": "2033-04-01",
            "end_date": "2033-04-30",
            "transaction_type": "supplier_invoice",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["transaction_id"] == str(expense_transaction.id)
    assert payload[0]["transaction_type"] == "supplier_invoice"
    assert Decimal(str(payload[0]["amount"])) == Decimal("4500.00")
    assert payload[0]["source_type"] == "supplier_invoice"
    assert payload[0]["source_layer"] == "financial_actual"


def test_dashboard_expense_source_returns_supplier_invoice_lines(
    client: TestClient,
    test_business_unit: BusinessUnitModel,
    test_unit_of_measure,
    create_supplier,
    create_inventory_item,
    create_purchase_invoice,
) -> None:
    supplier = create_supplier(
        business_unit_id=test_business_unit.id,
        name="Dashboard Source Supplier",
    )
    inventory_item = create_inventory_item(
        business_unit_id=test_business_unit.id,
        uom_id=test_unit_of_measure.id,
        name="Dashboard Source Flour",
        item_type="raw_material",
    )
    invoice = create_purchase_invoice(
        business_unit_id=test_business_unit.id,
        supplier_id=supplier.id,
        invoice_number="DASH-SOURCE-001",
        invoice_date=date(2034, 6, 7),
        currency="HUF",
        gross_total=Decimal("5600.00"),
        notes="Dashboard source drill-down invoice",
        lines=[
            {
                "inventory_item_id": inventory_item.id,
                "description": "Flour 10 kg",
                "quantity": Decimal("10.000"),
                "uom_id": test_unit_of_measure.id,
                "unit_net_amount": Decimal("500.00"),
                "line_net_amount": Decimal("5000.00"),
            },
            {
                "description": "Delivery fee",
                "quantity": Decimal("1.000"),
                "uom_id": test_unit_of_measure.id,
                "unit_net_amount": Decimal("600.00"),
                "line_net_amount": Decimal("600.00"),
            },
        ],
    )
    post_response = client.post(f"/api/v1/procurement/purchase-invoices/{invoice.id}/post")
    assert post_response.status_code == 200

    expenses_response = client.get(
        f"{API_PREFIX}/dashboard/expenses",
        params={
            "scope": "overall",
            "business_unit_id": str(test_business_unit.id),
            "period": "custom",
            "start_date": "2034-06-01",
            "end_date": "2034-06-30",
            "transaction_type": "supplier_invoice",
        },
    )
    assert expenses_response.status_code == 200
    expense_row = expenses_response.json()[0]

    source_response = client.get(
        f"{API_PREFIX}/dashboard/expense-source",
        params={"transaction_id": expense_row["transaction_id"]},
    )

    assert source_response.status_code == 200
    payload = source_response.json()
    assert payload["transaction_id"] == expense_row["transaction_id"]
    assert payload["source_type"] == "supplier_invoice"
    assert payload["source_id"] == str(invoice.id)
    assert payload["supplier_id"] == str(supplier.id)
    assert payload["supplier_name"] == "Dashboard Source Supplier"
    assert payload["invoice_number"] == "DASH-SOURCE-001"
    assert payload["invoice_date"] == "2034-06-07"
    assert Decimal(str(payload["gross_total"])) == Decimal("5600.00")
    assert len(payload["lines"]) == 2
    assert {line["description"] for line in payload["lines"]} == {
        "Delivery fee",
        "Flour 10 kg",
    }


def test_dashboard_basket_pairs_return_co_purchased_products(
    client: TestClient,
    analytics_data_builder: AnalyticsTestDataBuilder,
    test_business_unit: BusinessUnitModel,
) -> None:
    for row_number, receipt_no, product_name, amount in [
        (2, "BASKET-1001", "Croissant", Decimal("1200")),
        (3, "BASKET-1001", "Espresso", Decimal("750")),
        (4, "BASKET-1001", "Macaron", Decimal("900")),
        (5, "BASKET-1002", "Croissant", Decimal("1200")),
        (6, "BASKET-1002", "Espresso", Decimal("750")),
    ]:
        analytics_data_builder.create_pos_row(
            business_unit_id=test_business_unit.id,
            row_number=row_number,
            payload_date=date(2035, 7, 8),
            receipt_no=receipt_no,
            category_name="Dashboard Basket",
            product_name=product_name,
            quantity=Decimal("1"),
            gross_amount=amount,
        )

    response = client.get(
        f"{API_PREFIX}/dashboard/basket-pairs",
        params={
            "scope": "overall",
            "business_unit_id": str(test_business_unit.id),
            "period": "custom",
            "start_date": "2035-07-01",
            "end_date": "2035-07-31",
            "limit": 5,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 3
    assert payload[0]["product_a"] == "Croissant"
    assert payload[0]["product_b"] == "Espresso"
    assert payload[0]["basket_count"] == 2
    assert Decimal(str(payload[0]["total_gross_amount"])) == Decimal("3900")
    assert payload[0]["source_layer"] == "import_derived"


def test_dashboard_basket_pair_receipts_return_source_receipts(
    client: TestClient,
    analytics_data_builder: AnalyticsTestDataBuilder,
    test_business_unit: BusinessUnitModel,
) -> None:
    for row_number, receipt_no, product_name, amount in [
        (2, "BASKET-DETAIL-1", "Croissant", Decimal("1200")),
        (3, "BASKET-DETAIL-1", "Espresso", Decimal("750")),
        (4, "BASKET-DETAIL-1", "Macaron", Decimal("900")),
        (5, "BASKET-DETAIL-2", "Croissant", Decimal("1200")),
        (6, "BASKET-DETAIL-2", "Tea", Decimal("650")),
    ]:
        analytics_data_builder.create_pos_row(
            business_unit_id=test_business_unit.id,
            row_number=row_number,
            payload_date=date(2035, 8, 9),
            receipt_no=receipt_no,
            category_name="Dashboard Basket Detail",
            product_name=product_name,
            quantity=Decimal("1"),
            gross_amount=amount,
        )

    response = client.get(
        f"{API_PREFIX}/dashboard/basket-pair-receipts",
        params={
            "scope": "overall",
            "business_unit_id": str(test_business_unit.id),
            "period": "custom",
            "start_date": "2035-08-01",
            "end_date": "2035-08-31",
            "product_a": "Croissant",
            "product_b": "Espresso",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["receipt_no"] == "BASKET-DETAIL-1"
    assert payload[0]["date"] == "2035-08-09"
    assert Decimal(str(payload[0]["gross_amount"])) == Decimal("2850")
    assert Decimal(str(payload[0]["quantity"])) == Decimal("3")
    assert {line["product_name"] for line in payload[0]["lines"]} == {
        "Croissant",
        "Espresso",
        "Macaron",
    }
    assert payload[0]["source_layer"] == "import_derived"
