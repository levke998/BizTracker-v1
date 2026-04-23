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
from app.modules.imports.infrastructure.orm.import_batch_model import ImportBatchModel
from app.modules.imports.infrastructure.orm.import_file_model import ImportFileModel
from app.modules.imports.infrastructure.orm.import_row_error_model import (
    ImportRowErrorModel,
)
from app.modules.imports.infrastructure.orm.import_row_model import ImportRowModel
from app.modules.master_data.infrastructure.orm.business_unit_model import (
    BusinessUnitModel,
)
from app.modules.master_data.infrastructure.orm.category_model import CategoryModel
from app.modules.master_data.infrastructure.orm.location_model import LocationModel
from app.modules.master_data.infrastructure.orm.product_model import ProductModel
from app.modules.master_data.infrastructure.orm.unit_of_measure_model import (
    UnitOfMeasureModel,
)

__all__ = [
    "BusinessUnitModel",
    "CategoryModel",
    "ImportBatchModel",
    "ImportFileModel",
    "ImportRowErrorModel",
    "ImportRowModel",
    "LocationModel",
    "PermissionModel",
    "ProductModel",
    "RoleModel",
    "RolePermissionModel",
    "UnitOfMeasureModel",
    "UserModel",
    "UserRoleModel",
]
