"""Reference data bootstrap for stable master data records."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.inventory.infrastructure.orm.inventory_item_model import InventoryItemModel
from app.modules.master_data.infrastructure.orm.business_unit_model import (
    BusinessUnitModel,
)
from app.modules.master_data.infrastructure.orm.location_model import LocationModel
from app.modules.master_data.infrastructure.orm.unit_of_measure_model import (
    UnitOfMeasureModel,
)

BUSINESS_UNITS = (
    {
        "code": "gourmand",
        "name": "Gourmand Sutohaz es Kezmuves Cukraszat",
        "type": "bakery",
        "is_active": True,
    },
    {
        "code": "flow",
        "name": "Flow Music Club",
        "type": "music_club",
        "is_active": True,
    },
)

UNITS_OF_MEASURE = (
    {"code": "pcs", "name": "Piece", "symbol": "pcs"},
    {"code": "kg", "name": "Kilogram", "symbol": "kg"},
    {"code": "g", "name": "Gram", "symbol": "g"},
    {"code": "l", "name": "Litre", "symbol": "l"},
    {"code": "ml", "name": "Millilitre", "symbol": "ml"},
)

LOCATIONS = (
    {
        "business_unit_code": "gourmand",
        "name": "Gourmand fo hely",
        "kind": "store",
        "is_active": True,
    },
    {
        "business_unit_code": "flow",
        "name": "Flow venue",
        "kind": "venue",
        "is_active": True,
    },
)

INVENTORY_ITEMS = (
    {
        "business_unit_code": "gourmand",
        "name": "Flour",
        "item_type": "raw_material",
        "uom_code": "kg",
        "track_stock": True,
        "is_active": True,
    },
    {
        "business_unit_code": "gourmand",
        "name": "Butter",
        "item_type": "raw_material",
        "uom_code": "kg",
        "track_stock": True,
        "is_active": True,
    },
    {
        "business_unit_code": "gourmand",
        "name": "Cake Box",
        "item_type": "packaging",
        "uom_code": "pcs",
        "track_stock": True,
        "is_active": True,
    },
    {
        "business_unit_code": "gourmand",
        "name": "Croissant",
        "item_type": "finished_good",
        "uom_code": "pcs",
        "track_stock": True,
        "is_active": True,
    },
    {
        "business_unit_code": "gourmand",
        "name": "Macaron",
        "item_type": "finished_good",
        "uom_code": "pcs",
        "track_stock": True,
        "is_active": True,
    },
    {
        "business_unit_code": "flow",
        "name": "Draft Beer",
        "item_type": "finished_good",
        "uom_code": "l",
        "track_stock": True,
        "is_active": True,
    },
    {
        "business_unit_code": "flow",
        "name": "Wine Bottle",
        "item_type": "finished_good",
        "uom_code": "pcs",
        "track_stock": True,
        "is_active": True,
    },
    {
        "business_unit_code": "flow",
        "name": "Soft Drink Syrup",
        "item_type": "raw_material",
        "uom_code": "l",
        "track_stock": True,
        "is_active": True,
    },
    {
        "business_unit_code": "flow",
        "name": "Plastic Cup",
        "item_type": "packaging",
        "uom_code": "pcs",
        "track_stock": True,
        "is_active": True,
    },
)


@dataclass(frozen=True, slots=True)
class BootstrapSummary:
    """Simple summary returned by the bootstrap routine."""

    created_count: int
    updated_count: int


def bootstrap_reference_data(session: Session) -> BootstrapSummary:
    """Insert or update stable reference data in an idempotent way."""

    created_count = 0
    updated_count = 0

    with session.begin():
        for payload in BUSINESS_UNITS:
            _, created, updated = _upsert_business_unit(session, payload)
            created_count += int(created)
            updated_count += int(updated)

        for payload in UNITS_OF_MEASURE:
            created, updated = _upsert_unit_of_measure(session, payload)
            created_count += int(created)
            updated_count += int(updated)

        for payload in LOCATIONS:
            created, updated = _upsert_location(session, payload)
            created_count += int(created)
            updated_count += int(updated)

        for payload in INVENTORY_ITEMS:
            created, updated = _upsert_inventory_item(session, payload)
            created_count += int(created)
            updated_count += int(updated)

    return BootstrapSummary(created_count=created_count, updated_count=updated_count)


def _upsert_business_unit(
    session: Session,
    payload: dict[str, str | bool],
) -> tuple[BusinessUnitModel, bool, bool]:
    model = session.scalar(
        select(BusinessUnitModel).where(BusinessUnitModel.code == payload["code"])
    )
    if model is None:
        model = BusinessUnitModel(**payload)
        session.add(model)
        session.flush()
        return model, True, False

    changed = False
    for field in ("name", "type", "is_active"):
        value = payload[field]
        if getattr(model, field) != value:
            setattr(model, field, value)
            changed = True

    return model, False, changed


def _upsert_unit_of_measure(
    session: Session,
    payload: dict[str, str | None],
) -> tuple[bool, bool]:
    model = session.scalar(
        select(UnitOfMeasureModel).where(UnitOfMeasureModel.code == payload["code"])
    )
    if model is None:
        session.add(UnitOfMeasureModel(**payload))
        return True, False

    changed = False
    for field in ("name", "symbol"):
        value = payload[field]
        if getattr(model, field) != value:
            setattr(model, field, value)
            changed = True

    return False, changed


def _upsert_location(
    session: Session,
    payload: dict[str, str | bool],
) -> tuple[bool, bool]:
    business_unit = session.scalar(
        select(BusinessUnitModel).where(
            BusinessUnitModel.code == payload["business_unit_code"]
        )
    )
    if business_unit is None:
        raise RuntimeError(
            "Cannot create bootstrap location because business unit "
            f"{payload['business_unit_code']!r} does not exist."
        )

    model = session.scalar(
        select(LocationModel).where(
            LocationModel.business_unit_id == business_unit.id,
            LocationModel.name == payload["name"],
        )
    )
    if model is None:
        session.add(
            LocationModel(
                business_unit_id=business_unit.id,
                name=str(payload["name"]),
                kind=str(payload["kind"]),
                is_active=bool(payload["is_active"]),
            )
        )
        return True, False

    changed = False
    for field in ("kind", "is_active"):
        value = payload[field]
        if getattr(model, field) != value:
            setattr(model, field, value)
            changed = True

    return False, changed


def _upsert_inventory_item(
    session: Session,
    payload: dict[str, str | bool],
) -> tuple[bool, bool]:
    business_unit = session.scalar(
        select(BusinessUnitModel).where(
            BusinessUnitModel.code == payload["business_unit_code"]
        )
    )
    if business_unit is None:
        raise RuntimeError(
            "Cannot create bootstrap inventory item because business unit "
            f"{payload['business_unit_code']!r} does not exist."
        )

    unit_of_measure = session.scalar(
        select(UnitOfMeasureModel).where(UnitOfMeasureModel.code == payload["uom_code"])
    )
    if unit_of_measure is None:
        raise RuntimeError(
            "Cannot create bootstrap inventory item because unit of measure "
            f"{payload['uom_code']!r} does not exist."
        )

    model = session.scalar(
        select(InventoryItemModel).where(
            InventoryItemModel.business_unit_id == business_unit.id,
            InventoryItemModel.name == payload["name"],
        )
    )
    if model is None:
        session.add(
            InventoryItemModel(
                business_unit_id=business_unit.id,
                name=str(payload["name"]),
                item_type=str(payload["item_type"]),
                uom_id=unit_of_measure.id,
                track_stock=bool(payload["track_stock"]),
                is_active=bool(payload["is_active"]),
            )
        )
        return True, False

    changed = False
    updates = {
        "item_type": str(payload["item_type"]),
        "uom_id": unit_of_measure.id,
        "track_stock": bool(payload["track_stock"]),
        "is_active": bool(payload["is_active"]),
    }
    for field, value in updates.items():
        if getattr(model, field) != value:
            setattr(model, field, value)
            changed = True

    return False, changed
