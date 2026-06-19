# Alembic Revision History

Ez a fajl az elso Alembic revisionok torteneti sorrendjet rogziti. A tenyleges
igazsagforras a `backend/migrations/versions` konyvtar.

## Elso implementalt revisionok

1. `001_create_schemas`
   - schemas: `auth`, `core`, `ingest`, `analytics`
2. `002_auth_identity_base`
   - identity tables: `user`, `role`, `permission`, `user_role`, `role_permission`
3. `003_core_master_data_foundation`
   - master data: `business_unit`, `location`, `unit_of_measure`
4. `004_core_category_product_base`
   - master data: `category`, `product`
5. `005_ingest_imports_base`
   - import metadata: `import_batch`, `import_file`
6. `006_ingest_import_rows_parsing`
   - parse counters, `import_row`, `import_row_error`
7. `007_core_financial_tx_base`
   - `core.financial_transaction`
8. `008_core_financial_tx_currency`
   - financial transaction currency
9. `009_core_inventory_item_base`
   - `core.inventory_item`
10. `010_inventory_item_name_uq`
    - inventory item name uniqueness per business unit
11. `011_core_inventory_movement`
    - `core.inventory_movement`
12. `012_inventory_movement_note`
    - inventory movement note

## Aktualis allapot

- Az implementalt lanc jelenlegi headje:
  `034_core_inventory_variance_threshold`.
- A revisionok egyetlen linearis lancot alkotnak.
- Ures adatbazison a teljes lancot a repository gyokeri
  `scripts/validate.ps1` ellenorzi.
- Az `alembic_version.version_num` mezot az elso revision `VARCHAR(64)` tipusra
  boviti, mert a kesobbi revisionazonositok hosszabbak az Alembic
  alapertelmezett 32 karakteres meretenel.
