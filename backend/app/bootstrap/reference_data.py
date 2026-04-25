"""Reference data bootstrap for stable master data records."""

from __future__ import annotations

import os
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.security import hash_password, normalize_email
from app.bootstrap.catalog_data import (
    BUSINESS_UNITS,
    CATEGORIES,
    INVENTORY_ITEMS,
    LOCATIONS,
    PRODUCTS,
    RECIPES,
    UNITS_OF_MEASURE,
)
from app.modules.imports.infrastructure.orm.import_batch_model import ImportBatchModel
from app.modules.finance.infrastructure.orm.transaction_model import (
    FinancialTransactionModel,
)
from app.modules.inventory.infrastructure.orm.inventory_item_model import (
    InventoryItemModel,
)
from app.modules.inventory.infrastructure.orm.inventory_movement_model import (
    InventoryMovementModel,
)
from app.modules.identity.infrastructure.orm.permission_model import PermissionModel
from app.modules.identity.infrastructure.orm.role_model import RoleModel
from app.modules.identity.infrastructure.orm.role_permission_model import (
    RolePermissionModel,
)
from app.modules.identity.infrastructure.orm.user_model import UserModel
from app.modules.identity.infrastructure.orm.user_role_model import UserRoleModel
from app.modules.master_data.infrastructure.orm.business_unit_model import (
    BusinessUnitModel,
)
from app.modules.master_data.infrastructure.orm.category_model import CategoryModel
from app.modules.master_data.infrastructure.orm.location_model import LocationModel
from app.modules.master_data.infrastructure.orm.product_model import ProductModel
from app.modules.master_data.infrastructure.orm.unit_of_measure_model import (
    UnitOfMeasureModel,
)
from app.modules.procurement.infrastructure.orm.supplier_model import SupplierModel
from app.modules.production.infrastructure.orm.recipe_model import (
    RecipeIngredientModel,
    RecipeModel,
    RecipeVersionModel,
)


@dataclass(frozen=True, slots=True)
class BootstrapSummary:
    """Simple summary returned by the bootstrap routine."""

    created_count: int
    updated_count: int
    archived_count: int
    deleted_count: int


def bootstrap_reference_data(session: Session) -> BootstrapSummary:
    """Insert or update stable reference data in an idempotent way."""

    created_count = 0
    updated_count = 0
    archived_count = 0
    deleted_count = 0

    with session.begin():
        deleted_count += _cleanup_known_dummy_data(session)

        created, updated = _upsert_identity_foundation(session)
        created_count += created
        updated_count += updated
        session.flush()

        for payload in BUSINESS_UNITS:
            _, created, updated = _upsert_business_unit(session, payload)
            created_count += int(created)
            updated_count += int(updated)
        session.flush()

        for payload in UNITS_OF_MEASURE:
            created, updated = _upsert_unit_of_measure(session, payload)
            created_count += int(created)
            updated_count += int(updated)
        session.flush()

        for payload in LOCATIONS:
            created, updated = _upsert_location(session, payload)
            created_count += int(created)
            updated_count += int(updated)
        session.flush()

        for payload in CATEGORIES:
            created, updated = _upsert_category(session, payload)
            created_count += int(created)
            updated_count += int(updated)
        session.flush()

        for payload in INVENTORY_ITEMS:
            created, updated = _upsert_inventory_item(session, payload)
            created_count += int(created)
            updated_count += int(updated)
        session.flush()

        for payload in PRODUCTS:
            created, updated = _upsert_product(session, payload)
            created_count += int(created)
            updated_count += int(updated)
        session.flush()

        for payload in RECIPES:
            created, updated = _upsert_recipe(session, payload)
            created_count += created
            updated_count += updated

        # Bootstrap must seed and refresh stable reference data only. User-created
        # catalog records are operational data, so they must not be archived just
        # because they are absent from the seed catalog.

    return BootstrapSummary(
        created_count=created_count,
        updated_count=updated_count,
        archived_count=archived_count,
        deleted_count=deleted_count,
    )


def _upsert_identity_foundation(session: Session) -> tuple[int, int]:
    created_count = 0
    updated_count = 0

    permission_payloads = [
        {
            "code": "app.access",
            "name": "Application access",
            "description": "Can access the BizTracker internal application.",
        }
    ]
    role_payloads = [
        {
            "code": "admin",
            "name": "Admin",
            "description": "Internal administrator for MVP access.",
            "permission_codes": ["app.access"],
        },
        {
            "code": "internal",
            "name": "Internal user",
            "description": "Baseline internal user role for protected app access.",
            "permission_codes": ["app.access"],
        },
    ]

    permissions_by_code: dict[str, PermissionModel] = {}
    for payload in permission_payloads:
        permission, created, updated = _upsert_permission(session, payload)
        permissions_by_code[permission.code] = permission
        created_count += int(created)
        updated_count += int(updated)
    session.flush()

    roles_by_code: dict[str, RoleModel] = {}
    for payload in role_payloads:
        role, created, updated = _upsert_role(session, payload)
        roles_by_code[role.code] = role
        created_count += int(created)
        updated_count += int(updated)
    session.flush()

    for role_payload in role_payloads:
        role = roles_by_code[str(role_payload["code"])]
        for permission_code in role_payload["permission_codes"]:
            if _ensure_role_permission(
                session,
                role=role,
                permission=permissions_by_code[str(permission_code)],
            ):
                created_count += 1

    user, created, updated = _upsert_seed_admin_user(session)
    created_count += int(created)
    updated_count += int(updated)
    session.flush()

    for role_code in ("admin", "internal"):
        if _ensure_user_role(session, user=user, role=roles_by_code[role_code]):
            created_count += 1

    return created_count, updated_count


def _upsert_permission(
    session: Session,
    payload: dict[str, str],
) -> tuple[PermissionModel, bool, bool]:
    model = session.scalar(
        select(PermissionModel).where(PermissionModel.code == payload["code"])
    )
    if model is None:
        model = PermissionModel(**payload)
        session.add(model)
        return model, True, False

    changed = False
    for field in ("name", "description"):
        if getattr(model, field) != payload[field]:
            setattr(model, field, payload[field])
            changed = True
    return model, False, changed


def _upsert_role(
    session: Session,
    payload: dict[str, str | list[str]],
) -> tuple[RoleModel, bool, bool]:
    model = session.scalar(select(RoleModel).where(RoleModel.code == payload["code"]))
    if model is None:
        model = RoleModel(
            code=str(payload["code"]),
            name=str(payload["name"]),
            description=str(payload["description"]),
            is_active=True,
        )
        session.add(model)
        return model, True, False

    changed = False
    updates = {
        "name": str(payload["name"]),
        "description": str(payload["description"]),
        "is_active": True,
    }
    for field, value in updates.items():
        if getattr(model, field) != value:
            setattr(model, field, value)
            changed = True
    return model, False, changed


def _upsert_seed_admin_user(session: Session) -> tuple[UserModel, bool, bool]:
    email = normalize_email(os.getenv("BIZTRACKER_ADMIN_EMAIL", "admin@biztracker.local"))
    full_name = os.getenv("BIZTRACKER_ADMIN_FULL_NAME", "BizTracker Admin")
    password = os.getenv("BIZTRACKER_ADMIN_PASSWORD", "ChangeMe123!")

    model = session.scalar(select(UserModel).where(UserModel.email == email))
    if model is None:
        model = UserModel(
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
            is_active=True,
        )
        session.add(model)
        return model, True, False

    changed = False
    if model.full_name != full_name:
        model.full_name = full_name
        changed = True
    if not model.is_active:
        model.is_active = True
        changed = True
    return model, False, changed


def _ensure_user_role(session: Session, *, user: UserModel, role: RoleModel) -> bool:
    existing = session.get(UserRoleModel, {"user_id": user.id, "role_id": role.id})
    if existing is not None:
        return False

    session.add(UserRoleModel(user_id=user.id, role_id=role.id))
    return True


def _ensure_role_permission(
    session: Session,
    *,
    role: RoleModel,
    permission: PermissionModel,
) -> bool:
    existing = session.get(
        RolePermissionModel,
        {"role_id": role.id, "permission_id": permission.id},
    )
    if existing is not None:
        return False

    session.add(RolePermissionModel(role_id=role.id, permission_id=permission.id))
    return True


def _cleanup_known_dummy_data(session: Session) -> int:
    real_business_unit_ids = [
        business_unit.id
        for business_unit in session.scalars(
            select(BusinessUnitModel).where(
                BusinessUnitModel.code.in_(["gourmand", "flow"])
            )
        ).all()
    ]
    if not real_business_unit_ids:
        return 0

    deleted_count = 0
    deleted_count += (
        session.execute(
            delete(FinancialTransactionModel).where(
                FinancialTransactionModel.business_unit_id.in_(real_business_unit_ids),
                FinancialTransactionModel.source_type == "import_row",
            )
        ).rowcount
        or 0
    )
    deleted_count += (
        session.execute(
            delete(ImportBatchModel).where(
                ImportBatchModel.business_unit_id.in_(real_business_unit_ids)
            )
        ).rowcount
        or 0
    )
    deleted_count += (
        session.execute(
            delete(SupplierModel).where(
                SupplierModel.business_unit_id.in_(real_business_unit_ids),
                SupplierModel.name.like("Other Unit Supplier%"),
            )
        ).rowcount
        or 0
    )
    reusable_demo_item_ids = [
        item_id
        for item_id, in session.execute(
            select(InventoryItemModel.id).where(
                InventoryItemModel.business_unit_id.in_(real_business_unit_ids),
                InventoryItemModel.name.like("Reusable Demo Item%"),
                ~select(InventoryMovementModel.id)
                .where(
                    InventoryMovementModel.inventory_item_id == InventoryItemModel.id
                )
                .exists(),
            )
        ).all()
    ]
    if reusable_demo_item_ids:
        deleted_count += (
            session.execute(
                delete(InventoryItemModel).where(
                    InventoryItemModel.id.in_(reusable_demo_item_ids)
                )
            ).rowcount
            or 0
        )
    return deleted_count


def _archive_records_not_in_catalog(session: Session) -> int:
    archived_count = 0
    business_units = _business_units_by_code(session)

    for business_unit_code in ("gourmand", "flow"):
        business_unit = business_units[business_unit_code]

        category_names = {
            str(payload["name"])
            for payload in CATEGORIES
            if payload["business_unit_code"] == business_unit_code
        }
        archived_count += _archive_unknown_categories(
            session,
            business_unit.id,
            category_names,
        )

        product_skus = {
            str(payload["sku"])
            for payload in PRODUCTS
            if payload["business_unit_code"] == business_unit_code
        }
        archived_count += _archive_unknown_products(
            session,
            business_unit.id,
            product_skus,
        )

        inventory_item_names = {
            str(payload["name"])
            for payload in INVENTORY_ITEMS
            if payload["business_unit_code"] == business_unit_code
        }
        archived_count += _archive_unknown_inventory_items(
            session,
            business_unit.id,
            inventory_item_names,
        )

    return archived_count


def _archive_unknown_categories(
    session: Session,
    business_unit_id,
    allowed_names: set[str],
) -> int:
    models = session.scalars(
        select(CategoryModel).where(CategoryModel.business_unit_id == business_unit_id)
    ).all()
    changed = 0
    for model in models:
        should_be_active = model.name in allowed_names
        if model.is_active != should_be_active:
            model.is_active = should_be_active
            changed += 1
    return changed


def _archive_unknown_products(
    session: Session,
    business_unit_id,
    allowed_skus: set[str],
) -> int:
    models = session.scalars(
        select(ProductModel).where(ProductModel.business_unit_id == business_unit_id)
    ).all()
    changed = 0
    for model in models:
        should_be_active = model.sku in allowed_skus
        if model.is_active != should_be_active:
            model.is_active = should_be_active
            changed += 1
    return changed


def _archive_unknown_inventory_items(
    session: Session,
    business_unit_id,
    allowed_names: set[str],
) -> int:
    models = session.scalars(
        select(InventoryItemModel).where(
            InventoryItemModel.business_unit_id == business_unit_id
        )
    ).all()
    changed = 0
    for model in models:
        should_be_active = model.name in allowed_names
        if model.is_active != should_be_active:
            model.is_active = should_be_active
            changed += 1
    return changed


def _business_units_by_code(session: Session) -> dict[str, BusinessUnitModel]:
    return {
        business_unit.code: business_unit
        for business_unit in session.scalars(select(BusinessUnitModel)).all()
    }


def _units_by_code(session: Session) -> dict[str, UnitOfMeasureModel]:
    return {unit.code: unit for unit in session.scalars(select(UnitOfMeasureModel)).all()}


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
    business_unit = _get_business_unit(session, str(payload["business_unit_code"]))

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


def _upsert_category(
    session: Session,
    payload: dict[str, str],
) -> tuple[bool, bool]:
    business_unit = _get_business_unit(session, payload["business_unit_code"])

    model = session.scalar(
        select(CategoryModel).where(
            CategoryModel.business_unit_id == business_unit.id,
            CategoryModel.parent_id.is_(None),
            CategoryModel.name == payload["name"],
        )
    )
    if model is None:
        session.add(
            CategoryModel(
                business_unit_id=business_unit.id,
                parent_id=None,
                name=payload["name"],
                is_active=True,
            )
        )
        return True, False

    if not model.is_active:
        model.is_active = True
        return False, True

    return False, False


def _upsert_inventory_item(
    session: Session,
    payload: dict[str, str | bool],
) -> tuple[bool, bool]:
    business_unit = _get_business_unit(session, str(payload["business_unit_code"]))
    unit_of_measure = _get_unit_of_measure(session, str(payload["uom_code"]))

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
                default_unit_cost=_to_decimal_or_none(payload.get("default_unit_cost")),
                estimated_stock_quantity=_to_decimal_or_none(
                    payload.get("estimated_stock_quantity")
                ),
                is_active=bool(payload["is_active"]),
            )
        )
        return True, False

    changed = False
    updates = {
        "item_type": str(payload["item_type"]),
        "uom_id": unit_of_measure.id,
        "track_stock": bool(payload["track_stock"]),
        "default_unit_cost": _to_decimal_or_none(payload.get("default_unit_cost")),
        "estimated_stock_quantity": _to_decimal_or_none(
            payload.get("estimated_stock_quantity")
        ),
        "is_active": bool(payload["is_active"]),
    }
    for field, value in updates.items():
        if getattr(model, field) != value:
            setattr(model, field, value)
            changed = True

    return False, changed


def _upsert_product(
    session: Session,
    payload: dict[str, str | None],
) -> tuple[bool, bool]:
    business_unit = _get_business_unit(session, str(payload["business_unit_code"]))
    category = _get_category(session, business_unit.id, str(payload["category_name"]))
    sales_uom = _get_unit_of_measure(session, str(payload["sales_uom_code"]))

    model = session.scalar(
        select(ProductModel).where(
            ProductModel.business_unit_id == business_unit.id,
            ProductModel.sku == payload["sku"],
        )
    )
    values = {
        "category_id": category.id,
        "sales_uom_id": sales_uom.id,
        "name": str(payload["name"]),
        "product_type": str(payload["product_type"]),
        "sale_price_gross": _to_decimal_or_none(payload["sale_price_gross"]),
        "default_unit_cost": _to_decimal_or_none(payload["default_unit_cost"]),
        "currency": "HUF",
        "is_active": True,
    }
    if model is None:
        session.add(
            ProductModel(
                business_unit_id=business_unit.id,
                sku=str(payload["sku"]),
                **values,
            )
        )
        return True, False

    changed = False
    for field, value in values.items():
        if getattr(model, field) != value:
            setattr(model, field, value)
            changed = True

    return False, changed


def _upsert_recipe(
    session: Session,
    payload: dict,
) -> tuple[int, int]:
    created_count = 0
    updated_count = 0

    product = session.scalar(select(ProductModel).where(ProductModel.sku == payload["sku"]))
    if product is None:
        raise RuntimeError(f"Cannot create recipe for missing product sku {payload['sku']!r}.")

    recipe_name = f"{product.name} recept"
    recipe = session.scalar(
        select(RecipeModel).where(
            RecipeModel.product_id == product.id,
            RecipeModel.name == recipe_name,
        )
    )
    if recipe is None:
        recipe = RecipeModel(product_id=product.id, name=recipe_name, is_active=True)
        session.add(recipe)
        session.flush()
        created_count += 1
    elif not recipe.is_active:
        recipe.is_active = True
        updated_count += 1

    yield_uom = _get_unit_of_measure(session, payload["yield_uom_code"])
    version = session.scalar(
        select(RecipeVersionModel).where(
            RecipeVersionModel.recipe_id == recipe.id,
            RecipeVersionModel.version_no == 1,
        )
    )
    yield_quantity = Decimal(payload["yield_quantity"])
    if version is None:
        version = RecipeVersionModel(
            recipe_id=recipe.id,
            version_no=1,
            is_active=True,
            yield_quantity=yield_quantity,
            yield_uom_id=yield_uom.id,
            notes="Seeded from prods.docx demo catalog.",
        )
        session.add(version)
        session.flush()
        created_count += 1
    else:
        values = {
            "is_active": True,
            "yield_quantity": yield_quantity,
            "yield_uom_id": yield_uom.id,
            "notes": "Seeded from prods.docx demo catalog.",
        }
        for field, value in values.items():
            if getattr(version, field) != value:
                setattr(version, field, value)
                updated_count += 1

    allowed_inventory_item_ids = set()
    for ingredient_name, quantity, uom_code in payload["ingredients"]:
        inventory_item = _get_inventory_item(
            session,
            product.business_unit_id,
            ingredient_name,
        )
        uom = _get_unit_of_measure(session, uom_code)
        allowed_inventory_item_ids.add(inventory_item.id)
        ingredient = session.scalar(
            select(RecipeIngredientModel).where(
                RecipeIngredientModel.recipe_version_id == version.id,
                RecipeIngredientModel.inventory_item_id == inventory_item.id,
            )
        )
        ingredient_quantity = Decimal(quantity)
        if ingredient is None:
            session.add(
                RecipeIngredientModel(
                    recipe_version_id=version.id,
                    inventory_item_id=inventory_item.id,
                    quantity=ingredient_quantity,
                    uom_id=uom.id,
                )
            )
            created_count += 1
            continue

        if ingredient.quantity != ingredient_quantity or ingredient.uom_id != uom.id:
            ingredient.quantity = ingredient_quantity
            ingredient.uom_id = uom.id
            updated_count += 1

    stale_ingredients = session.scalars(
        select(RecipeIngredientModel).where(
            RecipeIngredientModel.recipe_version_id == version.id,
            RecipeIngredientModel.inventory_item_id.notin_(allowed_inventory_item_ids),
        )
    ).all()
    for ingredient in stale_ingredients:
        session.delete(ingredient)
        updated_count += 1

    return created_count, updated_count


def _get_business_unit(session: Session, code: str) -> BusinessUnitModel:
    model = session.scalar(select(BusinessUnitModel).where(BusinessUnitModel.code == code))
    if model is None:
        raise RuntimeError(f"Cannot find business unit {code!r}.")
    return model


def _get_unit_of_measure(session: Session, code: str) -> UnitOfMeasureModel:
    model = session.scalar(select(UnitOfMeasureModel).where(UnitOfMeasureModel.code == code))
    if model is None:
        raise RuntimeError(f"Cannot find unit of measure {code!r}.")
    return model


def _get_category(
    session: Session,
    business_unit_id,
    name: str,
) -> CategoryModel:
    model = session.scalar(
        select(CategoryModel).where(
            CategoryModel.business_unit_id == business_unit_id,
            CategoryModel.name == name,
        )
    )
    if model is None:
        raise RuntimeError(f"Cannot find category {name!r}.")
    return model


def _get_inventory_item(
    session: Session,
    business_unit_id,
    name: str,
) -> InventoryItemModel:
    model = session.scalar(
        select(InventoryItemModel).where(
            InventoryItemModel.business_unit_id == business_unit_id,
            InventoryItemModel.name == name,
        )
    )
    if model is None:
        raise RuntimeError(f"Cannot find inventory item {name!r}.")
    return model


def _to_decimal_or_none(value: str | None) -> Decimal | None:
    if value is None:
        return None
    return Decimal(value)
