"""Remove local demo data while preserving real POS imports."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.modules.events.infrastructure.orm.event_model import EventModel
from app.modules.finance.infrastructure.orm.transaction_model import (
    FinancialTransactionModel,
)
from app.modules.imports.infrastructure.orm.import_batch_model import ImportBatchModel
from app.modules.imports.infrastructure.orm.import_file_model import ImportFileModel
from app.modules.imports.infrastructure.orm.import_row_error_model import (
    ImportRowErrorModel,
)
from app.modules.imports.infrastructure.orm.import_row_model import ImportRowModel
from app.modules.inventory.infrastructure.orm.estimated_consumption_model import (
    EstimatedConsumptionAuditModel,
)
from app.modules.inventory.infrastructure.orm.inventory_item_model import (
    InventoryItemModel,
)
from app.modules.inventory.infrastructure.orm.inventory_movement_model import (
    InventoryMovementModel,
)
from app.modules.master_data.infrastructure.orm.business_unit_model import (
    BusinessUnitModel,
)
from app.modules.master_data.infrastructure.orm.category_model import CategoryModel
from app.modules.master_data.infrastructure.orm.location_model import LocationModel
from app.modules.master_data.infrastructure.orm.product_model import ProductModel
from app.modules.procurement.infrastructure.orm.purchase_invoice_line_model import (
    PurchaseInvoiceLineModel,
)
from app.modules.procurement.infrastructure.orm.purchase_invoice_model import (
    PurchaseInvoiceModel,
)
from app.modules.procurement.infrastructure.orm.supplier_model import SupplierModel
from app.modules.production.infrastructure.orm.recipe_model import (
    RecipeIngredientModel,
    RecipeModel,
    RecipeVersionModel,
)
from app.modules.weather.infrastructure.orm.weather_model import (
    WeatherLocationModel,
    WeatherObservationHourlyModel,
)


REAL_IMPORT_TYPES_BY_UNIT = {
    "gourmand": "gourmand_pos_sales",
    "flow": "flow_pos_sales",
}


@dataclass(slots=True)
class CleanupSummary:
    deleted: dict[str, int] = field(default_factory=dict)
    kept: dict[str, int] = field(default_factory=dict)

    def add_deleted(self, label: str, count: int | None) -> None:
        self.deleted[label] = self.deleted.get(label, 0) + int(count or 0)

    def add_kept(self, label: str, count: int) -> None:
        self.kept[label] = self.kept.get(label, 0) + count


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Commit the cleanup. Without this flag the transaction is rolled back.",
    )
    args = parser.parse_args()

    with SessionLocal() as session:
        summary = clean_demo_data(session)
        if args.apply:
            session.commit()
        else:
            session.rollback()
        print_summary(summary, applied=args.apply)


def clean_demo_data(session: Session) -> CleanupSummary:
    summary = CleanupSummary()
    business_units = {
        unit.code: unit
        for unit in session.scalars(select(BusinessUnitModel)).all()
    }
    real_units = [
        business_units[code]
        for code in ("gourmand", "flow")
        if code in business_units
    ]
    real_unit_ids = [unit.id for unit in real_units]

    if real_unit_ids:
        _delete_demo_import_batches(session, real_unit_ids, summary)
        _delete_synthetic_stock_outputs(session, real_unit_ids, summary)
        _delete_demo_recipes(session, real_unit_ids, summary)
        _delete_demo_inventory(session, real_unit_ids, summary)
        _delete_demo_procurement_seed(session, real_unit_ids, summary)
        _delete_demo_catalog_records(session, real_units, summary)
        _delete_demo_locations(session, real_unit_ids, summary)

    test_unit = business_units.get("test-integration")
    if test_unit is not None:
        _delete_business_unit_tree(session, [test_unit.id], summary)
        summary.add_deleted(
            "test_business_units",
            session.execute(
                delete(BusinessUnitModel).where(BusinessUnitModel.id == test_unit.id)
            ).rowcount,
        )

    return summary


def _delete_demo_import_batches(
    session: Session,
    business_unit_ids: list[UUID],
    summary: CleanupSummary,
) -> None:
    demo_batch_ids = [
        batch_id
        for batch_id, in session.execute(
            select(ImportBatchModel.id)
            .join(ImportFileModel, ImportFileModel.batch_id == ImportBatchModel.id)
            .where(
                ImportBatchModel.business_unit_id.in_(business_unit_ids),
                ImportBatchModel.import_type == "pos_sales",
                ImportFileModel.original_name.like("%.demo-pos-api.json"),
            )
            .distinct()
        ).all()
    ]
    failed_trial_batch_ids = [
        batch_id
        for batch_id, in session.execute(
            select(ImportBatchModel.id).where(
                ImportBatchModel.business_unit_id.in_(business_unit_ids),
                ImportBatchModel.import_type == "pos_sales",
                ImportBatchModel.parsed_rows == 0,
                ImportBatchModel.error_rows > 0,
            )
        ).all()
    ]
    batch_ids = list({*demo_batch_ids, *failed_trial_batch_ids})
    row_ids = _row_ids_for_batches(session, batch_ids)

    summary.add_kept(
        "real_import_batches",
        len(
            session.scalars(
                select(ImportBatchModel.id).where(
                    ImportBatchModel.import_type.in_(
                        REAL_IMPORT_TYPES_BY_UNIT.values()
                    )
                )
            ).all()
        ),
    )
    _delete_import_row_side_effects(session, row_ids, summary)
    _delete_import_batches(session, batch_ids, summary)


def _delete_synthetic_stock_outputs(
    session: Session,
    business_unit_ids: list[UUID],
    summary: CleanupSummary,
) -> None:
    summary.add_deleted(
        "estimated_consumption_audits",
        session.execute(
            delete(EstimatedConsumptionAuditModel).where(
                EstimatedConsumptionAuditModel.business_unit_id.in_(business_unit_ids)
            )
        ).rowcount,
    )
    summary.add_deleted(
        "inventory_movements",
        session.execute(
            delete(InventoryMovementModel).where(
                InventoryMovementModel.business_unit_id.in_(business_unit_ids)
            )
        ).rowcount,
    )


def _delete_demo_recipes(
    session: Session,
    business_unit_ids: list[UUID],
    summary: CleanupSummary,
) -> None:
    product_ids = [
        product_id
        for product_id, in session.execute(
            select(ProductModel.id).where(
                ProductModel.business_unit_id.in_(business_unit_ids)
            )
        ).all()
    ]
    recipe_ids = [
        recipe_id
        for recipe_id, in session.execute(
            select(RecipeModel.id).where(RecipeModel.product_id.in_(product_ids))
        ).all()
    ]
    version_ids = [
        version_id
        for version_id, in session.execute(
            select(RecipeVersionModel.id).where(
                RecipeVersionModel.recipe_id.in_(recipe_ids)
            )
        ).all()
    ]

    if version_ids:
        summary.add_deleted(
            "recipe_ingredients",
            session.execute(
                delete(RecipeIngredientModel).where(
                    RecipeIngredientModel.recipe_version_id.in_(version_ids)
                )
            ).rowcount,
        )
        summary.add_deleted(
            "recipe_versions",
            session.execute(
                delete(RecipeVersionModel).where(
                    RecipeVersionModel.id.in_(version_ids)
                )
            ).rowcount,
        )
    if recipe_ids:
        summary.add_deleted(
            "recipes",
            session.execute(delete(RecipeModel).where(RecipeModel.id.in_(recipe_ids))).rowcount,
        )


def _delete_demo_inventory(
    session: Session,
    business_unit_ids: list[UUID],
    summary: CleanupSummary,
) -> None:
    summary.add_deleted(
        "inventory_items",
        session.execute(
            delete(InventoryItemModel).where(
                InventoryItemModel.business_unit_id.in_(business_unit_ids)
            )
        ).rowcount,
    )


def _delete_demo_procurement_seed(
    session: Session,
    business_unit_ids: list[UUID],
    summary: CleanupSummary,
) -> None:
    invoice_ids = [
        invoice_id
        for invoice_id, in session.execute(
            select(PurchaseInvoiceModel.id).where(
                PurchaseInvoiceModel.business_unit_id.in_(business_unit_ids)
            )
        ).all()
    ]
    if invoice_ids:
        summary.add_deleted(
            "purchase_invoice_lines",
            session.execute(
                delete(PurchaseInvoiceLineModel).where(
                    PurchaseInvoiceLineModel.invoice_id.in_(invoice_ids)
                )
            ).rowcount,
        )
        summary.add_deleted(
            "purchase_invoices",
            session.execute(
                delete(PurchaseInvoiceModel).where(
                    PurchaseInvoiceModel.id.in_(invoice_ids)
                )
            ).rowcount,
        )
    summary.add_deleted(
        "suppliers",
        session.execute(
            delete(SupplierModel).where(
                SupplierModel.business_unit_id.in_(business_unit_ids)
            )
        ).rowcount,
    )


def _delete_demo_catalog_records(
    session: Session,
    real_units: list[BusinessUnitModel],
    summary: CleanupSummary,
) -> None:
    for unit in real_units:
        import_type = REAL_IMPORT_TYPES_BY_UNIT.get(unit.code)
        real_names, real_categories = _real_import_catalog(session, unit.id, import_type)
        products = session.scalars(
            select(ProductModel).where(ProductModel.business_unit_id == unit.id)
        ).all()
        product_ids_to_delete = [
            product.id
            for product in products
            if unit.code == "flow"
            or not product.is_active
            or _key(product.name) not in real_names
        ]
        summary.add_kept(f"{unit.code}_real_products", len(products) - len(product_ids_to_delete))
        if product_ids_to_delete:
            summary.add_deleted(
                f"{unit.code}_demo_products",
                session.execute(
                    delete(ProductModel).where(ProductModel.id.in_(product_ids_to_delete))
                ).rowcount,
            )

        categories = session.scalars(
            select(CategoryModel).where(CategoryModel.business_unit_id == unit.id)
        ).all()
        category_ids_to_delete = [
            category.id
            for category in categories
            if unit.code == "flow" or _key(category.name) not in real_categories
        ]
        summary.add_kept(
            f"{unit.code}_real_categories",
            len(categories) - len(category_ids_to_delete),
        )
        if category_ids_to_delete:
            summary.add_deleted(
                f"{unit.code}_demo_categories",
                session.execute(
                    delete(CategoryModel).where(
                        CategoryModel.id.in_(category_ids_to_delete)
                    )
                ).rowcount,
            )


def _delete_demo_locations(
    session: Session,
    business_unit_ids: list[UUID],
    summary: CleanupSummary,
) -> None:
    summary.add_deleted(
        "locations",
        session.execute(
            delete(LocationModel).where(LocationModel.business_unit_id.in_(business_unit_ids))
        ).rowcount,
    )


def _delete_business_unit_tree(
    session: Session,
    business_unit_ids: list[UUID],
    summary: CleanupSummary,
) -> None:
    batch_ids = [
        batch_id
        for batch_id, in session.execute(
            select(ImportBatchModel.id).where(
                ImportBatchModel.business_unit_id.in_(business_unit_ids)
            )
        ).all()
    ]
    row_ids = _row_ids_for_batches(session, batch_ids)
    _delete_import_row_side_effects(session, row_ids, summary)

    summary.add_deleted(
        "test_financial_transactions",
        session.execute(
            delete(FinancialTransactionModel).where(
                FinancialTransactionModel.business_unit_id.in_(business_unit_ids)
            )
        ).rowcount,
    )
    summary.add_deleted(
        "test_estimated_consumption_audits",
        session.execute(
            delete(EstimatedConsumptionAuditModel).where(
                EstimatedConsumptionAuditModel.business_unit_id.in_(business_unit_ids)
            )
        ).rowcount,
    )
    summary.add_deleted(
        "test_inventory_movements",
        session.execute(
            delete(InventoryMovementModel).where(
                InventoryMovementModel.business_unit_id.in_(business_unit_ids)
            )
        ).rowcount,
    )
    summary.add_deleted(
        "test_events",
        session.execute(
            delete(EventModel).where(EventModel.business_unit_id.in_(business_unit_ids))
        ).rowcount,
    )
    _delete_weather_for_business_units(session, business_unit_ids, summary)
    _delete_demo_procurement_seed(session, business_unit_ids, summary)
    _delete_demo_recipes(session, business_unit_ids, summary)
    summary.add_deleted(
        "test_products",
        session.execute(
            delete(ProductModel).where(ProductModel.business_unit_id.in_(business_unit_ids))
        ).rowcount,
    )
    _delete_demo_inventory(session, business_unit_ids, summary)
    summary.add_deleted(
        "test_categories",
        session.execute(
            delete(CategoryModel).where(
                CategoryModel.business_unit_id.in_(business_unit_ids)
            )
        ).rowcount,
    )
    _delete_demo_locations(session, business_unit_ids, summary)
    _delete_import_batches(session, batch_ids, summary)


def _delete_import_row_side_effects(
    session: Session,
    row_ids: list[UUID],
    summary: CleanupSummary,
) -> None:
    if not row_ids:
        return
    summary.add_deleted(
        "demo_financial_transactions",
        session.execute(
            delete(FinancialTransactionModel).where(
                FinancialTransactionModel.source_type == "import_row",
                FinancialTransactionModel.source_id.in_(row_ids),
            )
        ).rowcount,
    )


def _delete_weather_for_business_units(
    session: Session,
    business_unit_ids: list[UUID],
    summary: CleanupSummary,
) -> None:
    weather_location_ids = [
        weather_location_id
        for weather_location_id, in session.execute(
            select(WeatherLocationModel.id).where(
                WeatherLocationModel.business_unit_id.in_(business_unit_ids)
            )
        ).all()
    ]
    if not weather_location_ids:
        return
    summary.add_deleted(
        "test_weather_observations",
        session.execute(
            delete(WeatherObservationHourlyModel).where(
                WeatherObservationHourlyModel.weather_location_id.in_(weather_location_ids)
            )
        ).rowcount,
    )
    summary.add_deleted(
        "test_weather_locations",
        session.execute(
            delete(WeatherLocationModel).where(
                WeatherLocationModel.id.in_(weather_location_ids)
            )
        ).rowcount,
    )
    summary.add_deleted(
        "demo_import_estimated_consumption_audits",
        session.execute(
            delete(EstimatedConsumptionAuditModel).where(
                EstimatedConsumptionAuditModel.source_type == "import_row",
                EstimatedConsumptionAuditModel.source_id.in_(row_ids),
            )
        ).rowcount,
    )


def _delete_import_batches(
    session: Session,
    batch_ids: list[UUID],
    summary: CleanupSummary,
) -> None:
    if not batch_ids:
        return
    summary.add_deleted(
        "import_row_errors",
        session.execute(
            delete(ImportRowErrorModel).where(ImportRowErrorModel.batch_id.in_(batch_ids))
        ).rowcount,
    )
    summary.add_deleted(
        "import_rows",
        session.execute(
            delete(ImportRowModel).where(ImportRowModel.batch_id.in_(batch_ids))
        ).rowcount,
    )
    summary.add_deleted(
        "import_files",
        session.execute(
            delete(ImportFileModel).where(ImportFileModel.batch_id.in_(batch_ids))
        ).rowcount,
    )
    summary.add_deleted(
        "import_batches",
        session.execute(
            delete(ImportBatchModel).where(ImportBatchModel.id.in_(batch_ids))
        ).rowcount,
    )


def _row_ids_for_batches(session: Session, batch_ids: list[UUID]) -> list[UUID]:
    if not batch_ids:
        return []
    return [
        row_id
        for row_id, in session.execute(
            select(ImportRowModel.id).where(ImportRowModel.batch_id.in_(batch_ids))
        ).all()
    ]


def _real_import_catalog(
    session: Session,
    business_unit_id: UUID,
    import_type: str | None,
) -> tuple[set[str], set[str]]:
    if import_type is None:
        return set(), set()
    product_names: set[str] = set()
    category_names: set[str] = set()
    rows = session.scalars(
        select(ImportRowModel)
        .join(ImportBatchModel, ImportBatchModel.id == ImportRowModel.batch_id)
        .where(
            ImportBatchModel.business_unit_id == business_unit_id,
            ImportBatchModel.import_type == import_type,
            ImportRowModel.parse_status == "parsed",
        )
    ).all()
    for row in rows:
        payload = row.normalized_payload or {}
        product_name = _clean(payload.get("product_name"))
        category_name = _clean(payload.get("category_name"))
        if product_name:
            product_names.add(_key(product_name))
        if category_name:
            category_names.add(_key(category_name))
    return product_names, category_names


def _clean(value: object) -> str:
    return str(value or "").strip()


def _key(value: str) -> str:
    return value.strip().casefold()


def print_summary(summary: CleanupSummary, *, applied: bool) -> None:
    mode = "APPLIED" if applied else "DRY RUN"
    print(f"Demo data cleanup {mode}")
    print("Kept:")
    for label, count in sorted(summary.kept.items()):
        print(f"  {label}: {count}")
    print("Deleted:")
    for label, count in sorted(summary.deleted.items()):
        print(f"  {label}: {count}")


if __name__ == "__main__":
    main()
