"""Integration tests for procurement purchase invoice APIs."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.modules.master_data.infrastructure.orm.business_unit_model import (
    BusinessUnitModel,
)
from app.modules.master_data.infrastructure.orm.unit_of_measure_model import (
    UnitOfMeasureModel,
)
from app.modules.master_data.infrastructure.orm.vat_rate_model import VatRateModel
from app.modules.procurement.infrastructure.orm.supplier_model import SupplierModel
from app.modules.procurement.infrastructure.orm.supplier_item_alias_model import (
    SupplierItemAliasModel,
)

API_PREFIX = "/api/v1/procurement"


def _upload_pdf_draft(
    client: TestClient,
    *,
    business_unit_id,
    supplier_id=None,
    filename: str = "supplier-invoice.pdf",
) -> dict:
    data = {"business_unit_id": str(business_unit_id)}
    if supplier_id is not None:
        data["supplier_id"] = str(supplier_id)

    response = client.post(
        f"{API_PREFIX}/purchase-invoice-drafts/pdf",
        data=data,
        files={
            "file": (
                filename,
                b"%PDF-1.4\n%test invoice\n",
                "application/pdf",
            )
        },
    )
    assert response.status_code == 201
    return response.json()


def test_create_purchase_invoice_succeeds(
    client: TestClient,
    test_business_unit: BusinessUnitModel,
    test_unit_of_measure: UnitOfMeasureModel,
    create_supplier,
    create_inventory_item,
) -> None:
    supplier = create_supplier(
        business_unit_id=test_business_unit.id,
        name="Molnar Alapanyag Kft",
    )
    inventory_item = create_inventory_item(
        business_unit_id=test_business_unit.id,
        uom_id=test_unit_of_measure.id,
        name="Fine Flour",
        item_type="raw_material",
    )

    response = client.post(
        f"{API_PREFIX}/purchase-invoices",
        json={
            "business_unit_id": str(test_business_unit.id),
            "supplier_id": str(supplier.id),
            "invoice_number": "INV-2026-001",
            "invoice_date": "2026-04-23",
            "currency": "HUF",
            "gross_total": "12500.00",
            "notes": "Manual bakery purchase",
            "lines": [
                {
                    "inventory_item_id": str(inventory_item.id),
                    "description": "Fine Flour 25 kg",
                    "quantity": "25.000",
                    "uom_id": str(test_unit_of_measure.id),
                    "unit_net_amount": "400.00",
                    "line_net_amount": "10000.00",
                }
            ],
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["business_unit_id"] == str(test_business_unit.id)
    assert payload["supplier_id"] == str(supplier.id)
    assert payload["supplier_name"] == "Molnar Alapanyag Kft"
    assert payload["invoice_number"] == "INV-2026-001"
    assert payload["gross_total"] == "12500.00"
    assert payload["is_posted"] is False
    assert payload["posted_to_finance"] is False
    assert payload["posted_inventory_movement_count"] == 0
    assert len(payload["lines"]) == 1
    assert payload["lines"][0]["inventory_item_id"] == str(inventory_item.id)


def test_create_purchase_invoice_with_invalid_supplier_returns_not_found(
    client: TestClient,
    test_business_unit: BusinessUnitModel,
    test_unit_of_measure: UnitOfMeasureModel,
) -> None:
    response = client.post(
        f"{API_PREFIX}/purchase-invoices",
        json={
            "business_unit_id": str(test_business_unit.id),
            "supplier_id": str(uuid4()),
            "invoice_number": "INV-2026-404",
            "invoice_date": "2026-04-23",
            "currency": "HUF",
            "gross_total": "1000.00",
            "lines": [
                {
                    "description": "Test line",
                    "quantity": "1.000",
                    "uom_id": str(test_unit_of_measure.id),
                    "unit_net_amount": "1000.00",
                    "line_net_amount": "1000.00",
                }
            ],
        },
    )

    assert response.status_code == 404
    assert "Supplier" in response.json()["detail"]


def test_create_purchase_invoice_rejects_supplier_from_other_business_unit(
    client: TestClient,
    test_business_unit: BusinessUnitModel,
    gourmand_business_unit: BusinessUnitModel,
    test_unit_of_measure: UnitOfMeasureModel,
    create_supplier,
) -> None:
    supplier = create_supplier(
        business_unit_id=gourmand_business_unit.id,
        name=f"Other Unit Supplier {uuid4().hex[:8]}",
    )

    response = client.post(
        f"{API_PREFIX}/purchase-invoices",
        json={
            "business_unit_id": str(test_business_unit.id),
            "supplier_id": str(supplier.id),
            "invoice_number": "INV-2026-422",
            "invoice_date": "2026-04-23",
            "currency": "HUF",
            "gross_total": "1000.00",
            "lines": [
                {
                    "description": "Mismatch line",
                    "quantity": "1.000",
                    "uom_id": str(test_unit_of_measure.id),
                    "unit_net_amount": "1000.00",
                    "line_net_amount": "1000.00",
                }
            ],
        },
    )

    assert response.status_code == 422
    assert "does not belong" in response.json()["detail"]


def test_create_purchase_invoice_with_invalid_uom_returns_not_found(
    client: TestClient,
    test_business_unit: BusinessUnitModel,
    create_supplier,
) -> None:
    supplier = create_supplier(
        business_unit_id=test_business_unit.id,
        name="Uom Test Supplier",
    )

    response = client.post(
        f"{API_PREFIX}/purchase-invoices",
        json={
            "business_unit_id": str(test_business_unit.id),
            "supplier_id": str(supplier.id),
            "invoice_number": "INV-2026-UOM",
            "invoice_date": "2026-04-23",
            "currency": "HUF",
            "gross_total": "1000.00",
            "lines": [
                {
                    "description": "Unknown UOM line",
                    "quantity": "1.000",
                    "uom_id": str(uuid4()),
                    "unit_net_amount": "1000.00",
                    "line_net_amount": "1000.00",
                }
            ],
        },
    )

    assert response.status_code == 404
    assert "Unit of measure" in response.json()["detail"]


def test_create_purchase_invoice_rejects_duplicate_invoice_number_for_same_supplier(
    client: TestClient,
    test_business_unit: BusinessUnitModel,
    test_unit_of_measure: UnitOfMeasureModel,
    create_supplier,
) -> None:
    supplier = create_supplier(
        business_unit_id=test_business_unit.id,
        name="Duplicate Invoice Supplier",
    )
    payload = {
        "business_unit_id": str(test_business_unit.id),
        "supplier_id": str(supplier.id),
        "invoice_number": "INV-2026-DUP",
        "invoice_date": "2026-04-23",
        "currency": "HUF",
        "gross_total": "1000.00",
        "lines": [
            {
                "description": "Duplicate line",
                "quantity": "1.000",
                "uom_id": str(test_unit_of_measure.id),
                "unit_net_amount": "1000.00",
                "line_net_amount": "1000.00",
            }
        ],
    }

    first_response = client.post(f"{API_PREFIX}/purchase-invoices", json=payload)
    assert first_response.status_code == 201

    second_response = client.post(f"{API_PREFIX}/purchase-invoices", json=payload)
    assert second_response.status_code == 409
    assert "already exists" in second_response.json()["detail"]


def test_list_purchase_invoices_filters_and_orders_results(
    client: TestClient,
    test_business_unit: BusinessUnitModel,
    test_unit_of_measure: UnitOfMeasureModel,
    create_supplier,
    create_purchase_invoice,
) -> None:
    alpha_supplier = create_supplier(
        business_unit_id=test_business_unit.id,
        name="Alpha Trade",
    )
    beta_supplier = create_supplier(
        business_unit_id=test_business_unit.id,
        name="Beta Trade",
    )

    create_purchase_invoice(
        business_unit_id=test_business_unit.id,
        supplier_id=alpha_supplier.id,
        invoice_number="INV-2026-100",
        invoice_date=date(2026, 4, 22),
        currency="HUF",
        gross_total=Decimal("1200.00"),
        lines=[
            {
                "description": "Alpha line",
                "quantity": Decimal("1.000"),
                "uom_id": test_unit_of_measure.id,
                "unit_net_amount": Decimal("1000.00"),
                "line_net_amount": Decimal("1000.00"),
            }
        ],
    )
    create_purchase_invoice(
        business_unit_id=test_business_unit.id,
        supplier_id=beta_supplier.id,
        invoice_number="INV-2026-200",
        invoice_date=date(2026, 4, 23),
        currency="HUF",
        gross_total=Decimal("2400.00"),
        lines=[
            {
                "description": "Beta line",
                "quantity": Decimal("2.000"),
                "uom_id": test_unit_of_measure.id,
                "unit_net_amount": Decimal("1000.00"),
                "line_net_amount": Decimal("2000.00"),
            }
        ],
    )

    response = client.get(
        f"{API_PREFIX}/purchase-invoices",
        params={
            "business_unit_id": str(test_business_unit.id),
            "supplier_id": str(beta_supplier.id),
            "limit": 1,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["supplier_id"] == str(beta_supplier.id)
    assert payload[0]["invoice_number"] == "INV-2026-200"
    assert payload[0]["invoice_date"] == "2026-04-23"


def test_upload_purchase_invoice_pdf_creates_review_draft(
    client: TestClient,
    test_business_unit: BusinessUnitModel,
    create_supplier,
) -> None:
    supplier = create_supplier(
        business_unit_id=test_business_unit.id,
        name="PDF Draft Supplier",
    )

    response = client.post(
        f"{API_PREFIX}/purchase-invoice-drafts/pdf",
        data={
            "business_unit_id": str(test_business_unit.id),
            "supplier_id": str(supplier.id),
        },
        files={
            "file": (
                "supplier-invoice.pdf",
                b"%PDF-1.4\n%test invoice\n",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["business_unit_id"] == str(test_business_unit.id)
    assert payload["supplier_id"] == str(supplier.id)
    assert payload["original_name"] == "supplier-invoice.pdf"
    assert payload["mime_type"] == "application/pdf"
    assert payload["size_bytes"] > 0
    assert payload["status"] == "review_required"
    assert payload["extraction_status"] == "not_started"
    assert payload["review_payload"] == {"header": {}, "lines": []}

    list_response = client.get(
        f"{API_PREFIX}/purchase-invoice-drafts",
        params={"business_unit_id": str(test_business_unit.id)},
    )

    assert list_response.status_code == 200
    drafts = list_response.json()
    assert len(drafts) == 1
    assert drafts[0]["id"] == payload["id"]


def test_upload_purchase_invoice_pdf_rejects_non_pdf(
    client: TestClient,
    test_business_unit: BusinessUnitModel,
) -> None:
    response = client.post(
        f"{API_PREFIX}/purchase-invoice-drafts/pdf",
        data={"business_unit_id": str(test_business_unit.id)},
        files={"file": ("invoice.txt", b"not a pdf", "text/plain")},
    )

    assert response.status_code == 422
    assert "PDF" in response.json()["detail"]


def test_update_purchase_invoice_pdf_review_calculates_vat_lines(
    client: TestClient,
    db_session,
    test_business_unit: BusinessUnitModel,
    test_unit_of_measure: UnitOfMeasureModel,
    create_supplier,
    create_inventory_item,
) -> None:
    supplier = create_supplier(
        business_unit_id=test_business_unit.id,
        name="PDF Review Supplier",
    )
    inventory_item = create_inventory_item(
        business_unit_id=test_business_unit.id,
        uom_id=test_unit_of_measure.id,
        name="Fine Flour Review",
        item_type="raw_material",
    )
    vat_rate = db_session.scalar(select(VatRateModel).where(VatRateModel.code == "HU_27"))
    assert vat_rate is not None
    draft = _upload_pdf_draft(
        client,
        business_unit_id=test_business_unit.id,
        supplier_id=supplier.id,
    )

    response = client.put(
        f"{API_PREFIX}/purchase-invoice-drafts/{draft['id']}/review",
        json={
            "supplier_id": str(supplier.id),
            "invoice_number": "PDF-2026-001",
            "invoice_date": "2026-05-04",
            "currency": "HUF",
            "gross_total": "1270.00",
            "lines": [
                {
                    "description": "XY finomliszt 1 kg",
                    "supplier_product_name": "XY finomliszt BL55 1 kg",
                    "inventory_item_id": str(inventory_item.id),
                    "quantity": "1.000",
                    "uom_id": str(test_unit_of_measure.id),
                    "vat_rate_id": str(vat_rate.id),
                    "line_gross_amount": "1270.00",
                }
            ],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "review_ready"
    assert payload["supplier_id"] == str(supplier.id)
    review_payload = payload["review_payload"]
    assert review_payload["header"]["invoice_number"] == "PDF-2026-001"
    assert review_payload["header"]["gross_total"] == "1270.00"
    line = review_payload["lines"][0]
    assert line["inventory_item_id"] == str(inventory_item.id)
    assert line["line_net_amount"] == "1000.00"
    assert line["vat_amount"] == "270.00"
    assert line["line_gross_amount"] == "1270.00"
    assert line["calculation_status"] == "ok"
    assert line["calculation_issues"] == []

    alias = db_session.scalar(
        select(SupplierItemAliasModel).where(
            SupplierItemAliasModel.source_item_name == "XY finomliszt BL55 1 kg"
        )
    )
    assert alias is not None
    assert alias.supplier_id == supplier.id
    assert alias.inventory_item_id == inventory_item.id
    assert alias.internal_display_name == "XY finomliszt 1 kg"
    assert alias.status == "mapped"


def test_update_purchase_invoice_pdf_review_keeps_unknown_supplier_item_for_mapping(
    client: TestClient,
    db_session,
    test_business_unit: BusinessUnitModel,
    test_unit_of_measure: UnitOfMeasureModel,
    create_supplier,
) -> None:
    supplier = create_supplier(
        business_unit_id=test_business_unit.id,
        name="PDF Unknown Item Supplier",
    )
    vat_rate = db_session.scalar(select(VatRateModel).where(VatRateModel.code == "HU_27"))
    assert vat_rate is not None
    draft = _upload_pdf_draft(
        client,
        business_unit_id=test_business_unit.id,
        supplier_id=supplier.id,
    )

    response = client.put(
        f"{API_PREFIX}/purchase-invoice-drafts/{draft['id']}/review",
        json={
            "supplier_id": str(supplier.id),
            "invoice_number": "PDF-UNKNOWN-001",
            "invoice_date": "2026-05-04",
            "currency": "HUF",
            "gross_total": "1270.00",
            "lines": [
                {
                    "description": "TopJoy alma",
                    "supplier_product_name": "TopJoy alma 0.25l karton",
                    "quantity": "1.000",
                    "uom_id": str(test_unit_of_measure.id),
                    "vat_rate_id": str(vat_rate.id),
                    "line_gross_amount": "1270.00",
                }
            ],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "review_ready"
    line = payload["review_payload"]["lines"][0]
    assert line["inventory_item_id"] is None
    assert line["supplier_product_name"] == "TopJoy alma 0.25l karton"
    assert line["description"] == "TopJoy alma"

    alias = db_session.scalar(
        select(SupplierItemAliasModel).where(
            SupplierItemAliasModel.source_item_name == "TopJoy alma 0.25l karton"
        )
    )
    assert alias is not None
    assert alias.inventory_item_id is None
    assert alias.internal_display_name == "TopJoy alma"
    assert alias.status == "review_required"

    list_response = client.get(
        f"{API_PREFIX}/supplier-item-aliases",
        params={
            "business_unit_id": str(test_business_unit.id),
            "status": "review_required",
        },
    )
    assert list_response.status_code == 200
    aliases = list_response.json()
    assert any(item["source_item_name"] == "TopJoy alma 0.25l karton" for item in aliases)


def test_supplier_item_alias_can_be_mapped_to_inventory_item(
    client: TestClient,
    db_session,
    test_business_unit: BusinessUnitModel,
    test_unit_of_measure: UnitOfMeasureModel,
    create_supplier,
    create_inventory_item,
) -> None:
    supplier = create_supplier(
        business_unit_id=test_business_unit.id,
        name="Alias Mapping Supplier",
    )
    inventory_item = create_inventory_item(
        business_unit_id=test_business_unit.id,
        uom_id=test_unit_of_measure.id,
        name="TopJoy alma",
        item_type="beverage",
    )
    alias = SupplierItemAliasModel(
        business_unit_id=test_business_unit.id,
        supplier_id=supplier.id,
        inventory_item_id=None,
        source_item_name="TopJoy alma 0.25l karton",
        source_item_key="topjoy alma 0.25l karton",
        internal_display_name="TopJoy alma",
        status="review_required",
        mapping_confidence="manual_review",
        occurrence_count=1,
    )
    db_session.add(alias)
    db_session.commit()
    db_session.refresh(alias)

    response = client.patch(
        f"{API_PREFIX}/supplier-item-aliases/{alias.id}/mapping",
        json={
            "inventory_item_id": str(inventory_item.id),
            "internal_display_name": "TopJoy alma",
            "notes": "Manual review",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == str(alias.id)
    assert payload["inventory_item_id"] == str(inventory_item.id)
    assert payload["internal_display_name"] == "TopJoy alma"
    assert payload["status"] == "mapped"
    assert payload["mapping_confidence"] == "manual"


def test_update_purchase_invoice_pdf_review_marks_mismatched_vat_for_review(
    client: TestClient,
    db_session,
    test_business_unit: BusinessUnitModel,
    test_unit_of_measure: UnitOfMeasureModel,
    create_supplier,
) -> None:
    supplier = create_supplier(
        business_unit_id=test_business_unit.id,
        name="PDF Review Mismatch Supplier",
    )
    vat_rate = db_session.scalar(select(VatRateModel).where(VatRateModel.code == "HU_27"))
    assert vat_rate is not None
    draft = _upload_pdf_draft(
        client,
        business_unit_id=test_business_unit.id,
        supplier_id=supplier.id,
    )

    response = client.put(
        f"{API_PREFIX}/purchase-invoice-drafts/{draft['id']}/review",
        json={
            "supplier_id": str(supplier.id),
            "invoice_number": "PDF-2026-REVIEW",
            "invoice_date": "2026-05-04",
            "currency": "HUF",
            "gross_total": "1270.00",
            "lines": [
                {
                    "description": "Ellenorzendo sor",
                    "quantity": "1.000",
                    "uom_id": str(test_unit_of_measure.id),
                    "vat_rate_id": str(vat_rate.id),
                    "line_gross_amount": "1270.00",
                    "vat_amount": "300.00",
                }
            ],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "review_required"
    line = payload["review_payload"]["lines"][0]
    assert line["calculation_status"] == "review_needed"
    assert line["calculation_issues"] == ["vat_amount_mismatch"]


def test_create_purchase_invoice_from_pdf_review_succeeds(
    client: TestClient,
    db_session,
    test_business_unit: BusinessUnitModel,
    test_unit_of_measure: UnitOfMeasureModel,
    create_supplier,
    create_inventory_item,
) -> None:
    supplier = create_supplier(
        business_unit_id=test_business_unit.id,
        name="PDF Convert Supplier",
    )
    inventory_item = create_inventory_item(
        business_unit_id=test_business_unit.id,
        uom_id=test_unit_of_measure.id,
        name="PDF Convert Flour",
        item_type="raw_material",
    )
    vat_rate = db_session.scalar(select(VatRateModel).where(VatRateModel.code == "HU_27"))
    assert vat_rate is not None
    draft = _upload_pdf_draft(
        client,
        business_unit_id=test_business_unit.id,
        supplier_id=supplier.id,
    )
    review_response = client.put(
        f"{API_PREFIX}/purchase-invoice-drafts/{draft['id']}/review",
        json={
            "supplier_id": str(supplier.id),
            "invoice_number": "PDF-CONVERT-001",
            "invoice_date": "2026-05-04",
            "currency": "HUF",
            "gross_total": "1270.00",
            "lines": [
                {
                    "description": "XY finomliszt 1 kg",
                    "supplier_product_name": "XY finomliszt BL55 1 kg",
                    "inventory_item_id": str(inventory_item.id),
                    "quantity": "1.000",
                    "uom_id": str(test_unit_of_measure.id),
                    "vat_rate_id": str(vat_rate.id),
                    "line_gross_amount": "1270.00",
                }
            ],
        },
    )
    assert review_response.status_code == 200
    assert review_response.json()["status"] == "review_ready"

    response = client.post(
        f"{API_PREFIX}/purchase-invoice-drafts/{draft['id']}/create-purchase-invoice"
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["business_unit_id"] == str(test_business_unit.id)
    assert payload["supplier_id"] == str(supplier.id)
    assert payload["invoice_number"] == "PDF-CONVERT-001"
    assert payload["gross_total"] == "1270.00"
    assert payload["is_posted"] is False
    assert len(payload["lines"]) == 1
    line = payload["lines"][0]
    assert line["inventory_item_id"] == str(inventory_item.id)
    assert line["line_net_amount"] == "1000.00"
    assert line["vat_rate_id"] == str(vat_rate.id)
    assert line["vat_amount"] == "270.00"
    assert line["line_gross_amount"] == "1270.00"

    drafts_response = client.get(
        f"{API_PREFIX}/purchase-invoice-drafts",
        params={"business_unit_id": str(test_business_unit.id)},
    )
    converted_draft = next(
        item for item in drafts_response.json() if item["id"] == draft["id"]
    )
    assert converted_draft["status"] == "invoice_created"
    assert converted_draft["review_payload"]["purchase_invoice_id"] == payload["id"]


def test_create_purchase_invoice_from_pdf_review_requires_ready_draft(
    client: TestClient,
    test_business_unit: BusinessUnitModel,
    create_supplier,
) -> None:
    supplier = create_supplier(
        business_unit_id=test_business_unit.id,
        name="PDF Not Ready Supplier",
    )
    draft = _upload_pdf_draft(
        client,
        business_unit_id=test_business_unit.id,
        supplier_id=supplier.id,
    )

    response = client.post(
        f"{API_PREFIX}/purchase-invoice-drafts/{draft['id']}/create-purchase-invoice"
    )

    assert response.status_code == 422
    assert "review_ready" in response.json()["detail"]
