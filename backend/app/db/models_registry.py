"""Central ORM model registry for Alembic model discovery.

Importing model modules here ensures the metadata is populated before
autogenerate or migration-related tooling runs.
"""

from app.modules.identity.infrastructure.orm.permission_model import PermissionModel
from app.modules.identity.infrastructure.orm.role_model import RoleModel
from app.modules.identity.infrastructure.orm.role_permission_model import (
    RolePermissionModel,
)
from app.modules.identity.infrastructure.orm.user_model import UserModel
from app.modules.identity.infrastructure.orm.user_role_model import UserRoleModel
from app.modules.finance.infrastructure.orm.transaction_model import (
    FinancialTransactionModel,
)
from app.modules.imports.infrastructure.orm.import_batch_model import ImportBatchModel
from app.modules.imports.infrastructure.orm.import_file_model import ImportFileModel
from app.modules.imports.infrastructure.orm.import_row_error_model import (
    ImportRowErrorModel,
)
from app.modules.imports.infrastructure.orm.import_row_model import ImportRowModel
from app.modules.inventory.infrastructure.orm.inventory_movement_model import (
    InventoryMovementModel,
)
from app.modules.inventory.infrastructure.orm.inventory_item_model import InventoryItemModel
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
from app.modules.procurement.infrastructure.orm.purchase_invoice_model import (
    PurchaseInvoiceModel,
)
from app.modules.procurement.infrastructure.orm.purchase_invoice_line_model import (
    PurchaseInvoiceLineModel,
)
from app.modules.production.infrastructure.orm.recipe_model import (
    RecipeIngredientModel,
    RecipeModel,
    RecipeVersionModel,
)

__all__ = [
    "BusinessUnitModel",
    "CategoryModel",
    "FinancialTransactionModel",
    "ImportBatchModel",
    "ImportFileModel",
    "ImportRowErrorModel",
    "ImportRowModel",
    "InventoryItemModel",
    "InventoryMovementModel",
    "LocationModel",
    "PermissionModel",
    "PurchaseInvoiceLineModel",
    "PurchaseInvoiceModel",
    "ProductModel",
    "RecipeIngredientModel",
    "RecipeModel",
    "RecipeVersionModel",
    "RoleModel",
    "RolePermissionModel",
    "SupplierModel",
    "UnitOfMeasureModel",
    "UserModel",
    "UserRoleModel",
]
