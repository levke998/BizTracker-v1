"""Shared fixtures for backend integration tests."""

from __future__ import annotations

from collections.abc import Generator
from datetime import datetime
from pathlib import Path
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.modules.finance.infrastructure.orm.transaction_model import (
    FinancialTransactionModel,
)
from app.modules.events.infrastructure.orm.event_model import EventModel
from app.modules.events.infrastructure.orm.event_ticket_actual_model import (
    EventTicketActualModel,
)
from app.main import app
from app.modules.imports.infrastructure.orm.import_batch_model import ImportBatchModel
from app.modules.imports.infrastructure.orm.import_file_model import ImportFileModel
from app.modules.imports.infrastructure.orm.import_row_error_model import (
    ImportRowErrorModel,
)
from app.modules.imports.infrastructure.orm.import_row_model import ImportRowModel
from app.modules.inventory.infrastructure.orm.inventory_item_model import (
    InventoryItemModel,
)
from app.modules.inventory.infrastructure.orm.estimated_consumption_model import (
    EstimatedConsumptionAuditModel,
)
from app.modules.inventory.infrastructure.orm.inventory_movement_model import (
    InventoryMovementModel,
)
from app.modules.master_data.infrastructure.orm.business_unit_model import (
    BusinessUnitModel,
)
from app.modules.master_data.infrastructure.orm.product_model import ProductModel
from app.modules.master_data.infrastructure.orm.unit_of_measure_model import (
    UnitOfMeasureModel,
)
from app.modules.pos_ingestion.infrastructure.orm.pos_product_alias_model import (
    PosProductAliasModel,
)
from app.modules.procurement.infrastructure.orm.supplier_model import SupplierModel
from app.modules.procurement.infrastructure.orm.purchase_invoice_model import (
    PurchaseInvoiceModel,
)
from app.modules.procurement.infrastructure.orm.purchase_invoice_draft_model import (
    PurchaseInvoiceDraftModel,
)
from app.modules.procurement.infrastructure.orm.purchase_invoice_line_model import (
    PurchaseInvoiceLineModel,
)
from app.modules.procurement.infrastructure.orm.supplier_item_alias_model import (
    SupplierItemAliasModel,
)
from app.modules.production.infrastructure.orm.recipe_model import (
    RecipeIngredientModel,
    RecipeModel,
    RecipeVersionModel,
)
from app.modules.weather.infrastructure.orm.weather_model import (
    WeatherLocationModel,
    WeatherObservationHourlyModel,
)

TEST_BUSINESS_UNIT_CODE = "test-integration"
TEST_BUSINESS_UNIT_NAME = "Integration Test Unit"
TEST_BUSINESS_UNIT_TYPE = "test"


def _collect_import_file_paths(
    db_session: Session,
    *,
    business_unit_ids: list,
) -> list[Path]:
    """Return uploaded file paths for the given business units."""

    if not business_unit_ids:
        return []

    return [
        Path(stored_path)
        for stored_path, in db_session.execute(
            select(ImportFileModel.stored_path)
            .join(ImportBatchModel, ImportFileModel.batch_id == ImportBatchModel.id)
            .where(ImportBatchModel.business_unit_id.in_(business_unit_ids))
        ).all()
    ]


def _cleanup_business_unit_data(
    db_session: Session,
    *,
    business_unit_ids: list,
) -> list[Path]:
    """Delete finance/import test data for the given business units."""

    if not business_unit_ids:
        return []

    file_paths = _collect_import_file_paths(
        db_session,
        business_unit_ids=business_unit_ids,
    )
    file_paths.extend(
        Path(stored_path)
        for stored_path, in db_session.execute(
            select(PurchaseInvoiceDraftModel.stored_path).where(
                PurchaseInvoiceDraftModel.business_unit_id.in_(business_unit_ids)
            )
        ).all()
    )
    batch_ids = [
        batch_id
        for batch_id, in db_session.execute(
            select(ImportBatchModel.id).where(
                ImportBatchModel.business_unit_id.in_(business_unit_ids)
            )
        ).all()
    ]
    inventory_item_ids = [
        item_id
        for item_id, in db_session.execute(
            select(InventoryItemModel.id).where(
                InventoryItemModel.business_unit_id.in_(business_unit_ids)
            )
        ).all()
    ]

    db_session.execute(
        delete(FinancialTransactionModel).where(
            FinancialTransactionModel.business_unit_id.in_(business_unit_ids)
        )
    )
    db_session.execute(
        delete(InventoryMovementModel).where(
            InventoryMovementModel.business_unit_id.in_(business_unit_ids)
        )
    )
    if inventory_item_ids:
        db_session.execute(
            delete(InventoryMovementModel).where(
                InventoryMovementModel.inventory_item_id.in_(inventory_item_ids)
            )
        )
    db_session.execute(
        delete(EstimatedConsumptionAuditModel).where(
            EstimatedConsumptionAuditModel.business_unit_id.in_(business_unit_ids)
        )
    )
    db_session.execute(
        delete(PosProductAliasModel).where(
            PosProductAliasModel.business_unit_id.in_(business_unit_ids)
        )
    )
    db_session.execute(
        delete(SupplierItemAliasModel).where(
            SupplierItemAliasModel.business_unit_id.in_(business_unit_ids)
        )
    )
    event_ids = [
        event_id
        for event_id, in db_session.execute(
            select(EventModel.id).where(EventModel.business_unit_id.in_(business_unit_ids))
        ).all()
    ]
    if event_ids:
        db_session.execute(
            delete(EventTicketActualModel).where(
                EventTicketActualModel.event_id.in_(event_ids)
            )
        )
        db_session.execute(delete(EventModel).where(EventModel.id.in_(event_ids)))
    weather_location_ids = [
        weather_location_id
        for weather_location_id, in db_session.execute(
            select(WeatherLocationModel.id).where(
                WeatherLocationModel.business_unit_id.in_(business_unit_ids)
            )
        ).all()
    ]
    if weather_location_ids:
        db_session.execute(
            delete(WeatherObservationHourlyModel).where(
                WeatherObservationHourlyModel.weather_location_id.in_(weather_location_ids)
            )
        )
        db_session.execute(
            delete(WeatherLocationModel).where(
                WeatherLocationModel.id.in_(weather_location_ids)
            )
        )
    invoice_ids = [
        invoice_id
        for invoice_id, in db_session.execute(
            select(PurchaseInvoiceModel.id).where(
                PurchaseInvoiceModel.business_unit_id.in_(business_unit_ids)
            )
        ).all()
    ]
    if invoice_ids:
        db_session.execute(
            delete(PurchaseInvoiceLineModel).where(
                PurchaseInvoiceLineModel.invoice_id.in_(invoice_ids)
            )
        )
        db_session.execute(
            delete(PurchaseInvoiceModel).where(PurchaseInvoiceModel.id.in_(invoice_ids))
        )
    db_session.execute(
        delete(PurchaseInvoiceDraftModel).where(
            PurchaseInvoiceDraftModel.business_unit_id.in_(business_unit_ids)
        )
    )
    product_ids = [
        product_id
        for product_id, in db_session.execute(
            select(ProductModel.id).where(
                ProductModel.business_unit_id.in_(business_unit_ids)
            )
        ).all()
    ]
    if product_ids:
        recipe_ids = [
            recipe_id
            for recipe_id, in db_session.execute(
                select(RecipeModel.id).where(RecipeModel.product_id.in_(product_ids))
            ).all()
        ]
        if recipe_ids:
            recipe_version_ids = [
                recipe_version_id
                for recipe_version_id, in db_session.execute(
                    select(RecipeVersionModel.id).where(
                        RecipeVersionModel.recipe_id.in_(recipe_ids)
                    )
                ).all()
            ]
            if recipe_version_ids:
                db_session.execute(
                    delete(RecipeIngredientModel).where(
                        RecipeIngredientModel.recipe_version_id.in_(recipe_version_ids)
                    )
                )
                db_session.execute(
                    delete(RecipeVersionModel).where(
                        RecipeVersionModel.id.in_(recipe_version_ids)
                    )
                )
            db_session.execute(delete(RecipeModel).where(RecipeModel.id.in_(recipe_ids)))
        db_session.execute(delete(ProductModel).where(ProductModel.id.in_(product_ids)))
    db_session.execute(
        delete(InventoryItemModel).where(InventoryItemModel.id.in_(inventory_item_ids))
    )
    db_session.execute(
        delete(SupplierModel).where(SupplierModel.business_unit_id.in_(business_unit_ids))
    )

    if batch_ids:
        db_session.execute(
            delete(ImportRowErrorModel).where(ImportRowErrorModel.batch_id.in_(batch_ids))
        )
        db_session.execute(
            delete(ImportRowModel).where(ImportRowModel.batch_id.in_(batch_ids))
        )
        db_session.execute(
            delete(ImportFileModel).where(ImportFileModel.batch_id.in_(batch_ids))
        )
        db_session.execute(delete(ImportBatchModel).where(ImportBatchModel.id.in_(batch_ids)))

    db_session.commit()
    return file_paths


def _delete_business_units(
    db_session: Session,
    *,
    business_unit_ids: list,
) -> None:
    """Delete business units after their dependent test data is removed."""

    if not business_unit_ids:
        return

    db_session.execute(delete(BusinessUnitModel).where(BusinessUnitModel.id.in_(business_unit_ids)))
    db_session.commit()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Yield a FastAPI test client against the real app wiring."""

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Yield a direct SQLAlchemy session for verification and cleanup."""

    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def imports_fixtures_dir() -> Path:
    """Return the directory that stores CSV fixtures for import tests."""

    return Path(__file__).resolve().parent / "fixtures" / "imports"


@pytest.fixture
def upload_import_fixture(client: TestClient):
    """Return a small helper that uploads one CSV import fixture."""

    def _upload_import_fixture(
        *,
        business_unit_id,
        import_type: str,
        file_path: Path,
    ):
        with file_path.open("rb") as file_object:
            response = client.post(
                "/api/v1/imports/files",
                data={
                    "business_unit_id": str(business_unit_id),
                    "import_type": import_type,
                },
                files={
                    "file": (file_path.name, file_object, "text/csv"),
                },
            )

        return response

    return _upload_import_fixture


@pytest.fixture
def create_financial_transaction(db_session: Session):
    """Create one finance transaction directly for read-side integration tests."""

    def _create_financial_transaction(
        *,
        business_unit_id,
        transaction_type: str,
        source_type: str,
        occurred_at: datetime,
        amount: Decimal,
        description: str,
        direction: str = "inflow",
        currency: str = "HUF",
    ) -> FinancialTransactionModel:
        transaction = FinancialTransactionModel(
            business_unit_id=business_unit_id,
            direction=direction,
            transaction_type=transaction_type,
            amount=amount,
            currency=currency,
            occurred_at=occurred_at,
            description=description,
            source_type=source_type,
            source_id=uuid4(),
        )
        db_session.add(transaction)
        db_session.commit()
        db_session.refresh(transaction)
        return transaction

    return _create_financial_transaction


@pytest.fixture
def test_unit_of_measure(db_session: Session) -> Generator[UnitOfMeasureModel, None, None]:
    """Create one temporary unit of measure for inventory tests."""

    unit = UnitOfMeasureModel(
        code=f"test-uom-{uuid4().hex[:8]}",
        name="Test Unit Of Measure",
        symbol="tu",
    )
    db_session.add(unit)
    db_session.commit()
    db_session.refresh(unit)

    yield unit

    db_session.rollback()
    db_session.expire_all()
    db_session.execute(
        delete(InventoryMovementModel).where(InventoryMovementModel.uom_id == unit.id)
    )
    item_ids = [
        item_id
        for item_id, in db_session.execute(
            select(InventoryItemModel.id).where(InventoryItemModel.uom_id == unit.id)
        ).all()
    ]
    if item_ids:
        db_session.execute(
            delete(InventoryMovementModel).where(
                InventoryMovementModel.inventory_item_id.in_(item_ids)
            )
        )
    purchase_invoice_line_filters = [PurchaseInvoiceLineModel.uom_id == unit.id]
    if item_ids:
        purchase_invoice_line_filters.append(
            PurchaseInvoiceLineModel.inventory_item_id.in_(item_ids)
        )
    invoice_ids = [
        invoice_id
        for invoice_id, in db_session.execute(
            select(PurchaseInvoiceLineModel.invoice_id).where(*purchase_invoice_line_filters)
        ).all()
    ]
    if invoice_ids:
        db_session.execute(
            delete(PurchaseInvoiceLineModel).where(
                PurchaseInvoiceLineModel.invoice_id.in_(invoice_ids)
            )
        )
        db_session.execute(
            delete(PurchaseInvoiceModel).where(PurchaseInvoiceModel.id.in_(invoice_ids))
        )
    db_session.execute(delete(InventoryItemModel).where(InventoryItemModel.uom_id == unit.id))
    db_session.execute(delete(UnitOfMeasureModel).where(UnitOfMeasureModel.id == unit.id))
    db_session.commit()


@pytest.fixture
def create_inventory_item(db_session: Session):
    """Create one inventory item directly for read-side integration tests."""

    def _create_inventory_item(
        *,
        business_unit_id,
        uom_id,
        name: str,
        item_type: str,
        track_stock: bool = True,
        is_active: bool = True,
    ) -> InventoryItemModel:
        item = InventoryItemModel(
            business_unit_id=business_unit_id,
            name=name,
            item_type=item_type,
            uom_id=uom_id,
            track_stock=track_stock,
            is_active=is_active,
        )
        db_session.add(item)
        db_session.commit()
        db_session.refresh(item)
        return item

    return _create_inventory_item


@pytest.fixture
def create_inventory_movement(db_session: Session):
    """Create one inventory movement directly for stock-level integration tests."""

    def _create_inventory_movement(
        *,
        business_unit_id,
        inventory_item_id,
        uom_id,
        movement_type: str,
        quantity: Decimal,
        occurred_at: datetime,
        unit_cost: Decimal | None = None,
        note: str | None = None,
    ) -> InventoryMovementModel:
        movement = InventoryMovementModel(
            business_unit_id=business_unit_id,
            inventory_item_id=inventory_item_id,
            movement_type=movement_type,
            quantity=quantity,
            uom_id=uom_id,
            unit_cost=unit_cost,
            note=note,
            occurred_at=occurred_at,
        )
        db_session.add(movement)
        db_session.commit()
        db_session.refresh(movement)
        return movement

    return _create_inventory_movement


@pytest.fixture
def create_supplier(db_session: Session):
    """Create one supplier directly for procurement integration tests."""

    def _create_supplier(
        *,
        business_unit_id,
        name: str,
        tax_id: str | None = None,
        contact_name: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        notes: str | None = None,
        is_active: bool = True,
    ) -> SupplierModel:
        supplier = SupplierModel(
            business_unit_id=business_unit_id,
            name=name,
            tax_id=tax_id,
            contact_name=contact_name,
            email=email,
            phone=phone,
            notes=notes,
            is_active=is_active,
        )
        db_session.add(supplier)
        db_session.commit()
        db_session.refresh(supplier)
        return supplier

    return _create_supplier


@pytest.fixture
def create_purchase_invoice(db_session: Session):
    """Create one purchase invoice directly for procurement integration tests."""

    def _create_purchase_invoice(
        *,
        business_unit_id,
        supplier_id,
        invoice_number: str,
        invoice_date,
        currency: str,
        gross_total,
        notes: str | None = None,
        lines: list[dict],
    ) -> PurchaseInvoiceModel:
        invoice = PurchaseInvoiceModel(
            business_unit_id=business_unit_id,
            supplier_id=supplier_id,
            invoice_number=invoice_number,
            invoice_date=invoice_date,
            currency=currency,
            gross_total=gross_total,
            notes=notes,
            lines=[
                PurchaseInvoiceLineModel(
                    inventory_item_id=line.get("inventory_item_id"),
                    description=line["description"],
                    quantity=line["quantity"],
                    uom_id=line["uom_id"],
                    unit_net_amount=line["unit_net_amount"],
                    line_net_amount=line["line_net_amount"],
                )
                for line in lines
            ],
        )
        db_session.add(invoice)
        db_session.commit()
        db_session.refresh(invoice)
        return invoice

    return _create_purchase_invoice


@pytest.fixture
def gourmand_business_unit(db_session: Session) -> BusinessUnitModel:
    """Return the seeded Gourmand business unit."""

    business_unit = db_session.scalar(
        select(BusinessUnitModel).where(BusinessUnitModel.code == "gourmand")
    )
    if business_unit is None:
        raise RuntimeError("Expected seeded 'gourmand' business unit to exist.")
    return business_unit


@pytest.fixture
def pcs_unit_of_measure(db_session: Session) -> UnitOfMeasureModel:
    """Return the seeded pcs unit of measure."""

    unit = db_session.scalar(
        select(UnitOfMeasureModel).where(UnitOfMeasureModel.code == "pcs")
    )
    if unit is None:
        raise RuntimeError("Expected seeded 'pcs' unit of measure to exist.")
    return unit


@pytest.fixture
def test_business_unit(db_session: Session) -> Generator[BusinessUnitModel, None, None]:
    """Return one stable shared test business unit and clean only its test data."""

    business_unit = db_session.scalar(
        select(BusinessUnitModel).where(BusinessUnitModel.code == TEST_BUSINESS_UNIT_CODE)
    )
    if business_unit is None:
        business_unit = BusinessUnitModel(
            code=TEST_BUSINESS_UNIT_CODE,
            name=TEST_BUSINESS_UNIT_NAME,
            type=TEST_BUSINESS_UNIT_TYPE,
            is_active=True,
        )
        db_session.add(business_unit)
        db_session.commit()
        db_session.refresh(business_unit)

    legacy_test_business_unit_ids = [
        business_unit_id
        for business_unit_id, in db_session.execute(
            select(BusinessUnitModel.id)
            .where(BusinessUnitModel.type == TEST_BUSINESS_UNIT_TYPE)
            .where(BusinessUnitModel.code != TEST_BUSINESS_UNIT_CODE)
        ).all()
    ]

    legacy_file_paths = _cleanup_business_unit_data(
        db_session,
        business_unit_ids=legacy_test_business_unit_ids,
    )
    _delete_business_units(
        db_session,
        business_unit_ids=legacy_test_business_unit_ids,
    )

    current_file_paths = _cleanup_business_unit_data(
        db_session,
        business_unit_ids=[business_unit.id],
    )

    for file_path in [*legacy_file_paths, *current_file_paths]:
        if file_path.exists():
            file_path.unlink()

    yield business_unit

    db_session.rollback()
    db_session.expire_all()

    file_paths = _cleanup_business_unit_data(
        db_session,
        business_unit_ids=[business_unit.id],
    )
    for file_path in file_paths:
        if file_path.exists():
            file_path.unlink()
