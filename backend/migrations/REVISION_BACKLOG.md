# Alembic Revision Backlog

Ez a fájl a tervezett első Alembic revisionök sorrendjét rögzíti. A cél, hogy a migration munka implementáció közben is ugyanazt a sorrendet kövesse.

## Planned revisions

1. `001_create_schemas`
   - create schemas: `auth`, `core`, `ingest`, `analytics`
2. `002_auth_identity_base`
   - create identity tables: `user`, `role`, `permission`, `user_role`, `role_permission`
3. `003_core_master_data_foundation`
   - create master data tables: `business_unit`, `location`, `unit_of_measure`
4. `004_core_category_product_base`
   - create master data tables: `category`, `product`
5. `005_ingest_imports_base`
   - create import metadata tables: `import_batch`, `import_file`
6. `006_ingest_import_rows_parsing`
   - add parse counters and create `import_row`, `import_row_error`

## Dependencies

- `002_auth_identity_base` depends on `001_create_schemas`
- `003_core_master_data_foundation` depends on `002_auth_identity_base`
- `004_core_category_product_base` depends on `003_core_master_data_foundation`
- `005_ingest_imports_base` depends on `004_core_category_product_base`
- `006_ingest_import_rows_parsing` depends on `005_ingest_imports_base`

## Notes

- These are planned revisions, not implemented Alembic version scripts yet.
- The detailed reasoning remains documented in [IDENTITY_CORE_MODEL_PLAN.md](C:\BizTracker\docs\IDENTITY_CORE_MODEL_PLAN.md).
