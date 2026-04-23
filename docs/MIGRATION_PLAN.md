# BizTracker Database Schema and Alembic Migration Plan
Current status:
- [CURRENT_STATUS.md](C:\BizTracker\docs\CURRENT_STATUS.md)

Ez a dokumentum az első adatbázis-séma és Alembic migration stratégiát rögzíti. A cél, hogy a sémát ne egyszerre, túl nagy csomagokban vezessük be, hanem modulárisan, jól áttekinthető migration hullámokban.

Kapcsolódó dokumentumok:
- [PROJECT_DESCRIPTION.md](C:\BizTracker\PROJECT_DESCRIPTION.md)
- [ARCHITECTURE.md](C:\BizTracker\docs\ARCHITECTURE.md)
- [MVP_IMPLEMENTATION_PLAN.md](C:\BizTracker\docs\MVP_IMPLEMENTATION_PLAN.md)

## 1. Migration tervezési alapelvek

- a migration csomagolás modul- és felelősségalapú legyen
- az első hullámok csak a tényleg szükséges táblákat hozzák be
- a domain-kockázatos részek későbbi migration hullámba kerüljenek
- az `analytics` ne legyen kezdetben túlmodellezve
- az Alembic revisionök legyenek kicsik, egyértelműek és visszakövethetők

## 2. Javasolt sémák

Javasolt PostgreSQL sémák:
- `auth`
- `core`
- `ingest`
- `analytics`

Szerepük:
- `auth`: felhasználók, role-ok, permissionök, tokenhez kapcsolódó auth rekordok
- `core`: operatív üzleti igazság
- `ingest`: import batch, nyers és hibaadatok
- `analytics`: read model, aggregált vagy snapshot jellegű táblák

## 3. Első migration hullám

Az első hullám célja a platform alap és a legfontosabb MVP modulok támogatása.

### 3.1. Elsőként bekerülő táblák

#### Auth csomag
- `auth.user`
- `auth.role`
- `auth.permission`
- `auth.user_role`
- `auth.role_permission`

#### Core master data csomag
- `core.business_unit`
- `core.location`
- `core.unit_of_measure`
- `core.category`
- `core.product`

#### Imports csomag
- `ingest.import_batch`
- `ingest.import_file`
- `ingest.import_row_error`

#### Finance csomag
- `core.financial_transaction`

#### Inventory csomag
- `core.inventory_item`
- `core.warehouse`
- `core.stock_movement`

#### Procurement csomag
- `core.supplier`
- `core.supplier_invoice`

### 3.2. Miért ezek kerülnek előre

- ezek közvetlenül támogatják az authot, importot, pénzügyi és készlet alapokat
- ezekből már építhető dashboard minimum és üzleti összehasonlítás
- ezek nem kényszerítenek túl korai, mély domain-döntéseket a production és events terén

## 4. Későbbi migration hullámok

### 4.1. Második hullám

#### Procurement bővítés
- `core.purchase_order`
- `core.purchase_order_line`

#### Inventory bővítés
- opcionális `core.inventory_snapshot`
- opcionális leltár táblák, ha tényleg szükséges

#### Analytics minimum
- `analytics.daily_business_kpi`
- `analytics.product_sales_fact`
- `analytics.category_sales_fact`

### 4.2. Harmadik hullám

#### Production
- `core.recipe`
- `core.recipe_version`
- `core.recipe_ingredient`
- `core.production_batch`
- `core.batch_consumption`
- `core.batch_output`
- `core.waste_record`

### 4.3. Negyedik hullám

#### Events
- `core.event`
- `core.performer`
- `core.event_performer`
- `core.ticket_sale_summary`
- `core.bar_sale_summary`
- `core.event_expense`
- `core.event_settlement`

### 4.4. Későbbi analitikai hullám

- `analytics.event_performance_fact`
- `analytics.weather_observation`
- `analytics.weather_sales_correlation_snapshot`
- későbbi prediktív és ajánlási snapshot táblák

## 5. Javasolt migration csomagolás

Az ajánlott Alembic csomagolás:

1. `001_create_schemas`
   - `auth`, `core`, `ingest`, `analytics`
2. `002_auth_identity_base`
   - user, role, permission, kapcsolótáblák
3. `003_core_master_data_base`
   - business_unit, location, unit_of_measure, category, product
4. `004_ingest_imports_base`
   - import_batch, import_file, import_row_error
5. `005_finance_base`
   - financial_transaction
6. `006_inventory_base`
   - inventory_item, warehouse, stock_movement
7. `007_procurement_base`
   - supplier, supplier_invoice
8. `008_analytics_base`
   - daily_business_kpi, product_sales_fact, category_sales_fact vagy ezek minimum kezdő változatai
9. `009_production_base`
   - recipe, recipe_version, recipe_ingredient, production_batch
10. `010_production_inventory_links`
   - batch_consumption, batch_output, waste_record
11. `011_events_base`
   - event, performer, event_performer
12. `012_events_financials`
   - ticket_sale_summary, bar_sale_summary, event_expense, event_settlement

Ez a sorrend jól illeszkedik az MVP implementációs sorrendhez.

## 6. Javasolt első migration backlog táblaszinten

### 6.1. `001_create_schemas`

Létrehozza:
- `auth`
- `core`
- `ingest`
- `analytics`

### 6.2. `002_auth_identity_base`

Létrehozza:
- `auth.user`
  - `id`
  - `email`
  - `password_hash`
  - `full_name`
  - `is_active`
  - `created_at`
  - `updated_at`
- `auth.role`
  - `id`
  - `code`
  - `name`
- `auth.permission`
  - `id`
  - `code`
  - `name`
- `auth.user_role`
  - `user_id`
  - `role_id`
- `auth.role_permission`
  - `role_id`
  - `permission_id`

### 6.3. `003_core_master_data_base`

Létrehozza:
- `core.business_unit`
  - `id`
  - `code`
  - `name`
  - `type`
  - `is_active`
- `core.location`
  - `id`
  - `business_unit_id`
  - `name`
  - `kind`
  - `is_active`
- `core.unit_of_measure`
  - `id`
  - `code`
  - `name`
- `core.category`
  - `id`
  - `business_unit_id`
  - `parent_id`
  - `name`
  - `is_active`
- `core.product`
  - `id`
  - `business_unit_id`
  - `category_id`
  - `sku`
  - `name`
  - `product_type`
  - `is_active`

### 6.4. `004_ingest_imports_base`

Létrehozza:
- `ingest.import_batch`
  - `id`
  - `business_unit_id`
  - `import_type`
  - `status`
  - `started_at`
  - `finished_at`
  - `created_by`
- `ingest.import_file`
  - `id`
  - `batch_id`
  - `original_name`
  - `stored_path`
  - `mime_type`
  - `uploaded_at`
- `ingest.import_row_error`
  - `id`
  - `batch_id`
  - `row_number`
  - `field_name`
  - `error_code`
  - `message`
  - `raw_payload`

### 6.5. `005_finance_base`

Létrehozza:
- `core.financial_transaction`
  - `id`
  - `business_unit_id`
  - `location_id`
  - `direction`
  - `transaction_type`
  - `source_type`
  - `source_id`
  - `amount`
  - `currency`
  - `occurred_at`
  - `description`
  - `created_at`

### 6.6. `006_inventory_base`

Létrehozza:
- `core.inventory_item`
  - `id`
  - `business_unit_id`
  - `name`
  - `item_type`
  - `uom_id`
  - `track_stock`
  - `is_active`
- `core.warehouse`
  - `id`
  - `location_id`
  - `name`
  - `is_active`
- `core.stock_movement`
  - `id`
  - `warehouse_id`
  - `inventory_item_id`
  - `movement_type`
  - `qty`
  - `unit_cost`
  - `occurred_at`
  - `source_type`
  - `source_id`
  - `note`

### 6.7. `007_procurement_base`

Létrehozza:
- `core.supplier`
  - `id`
  - `business_unit_id`
  - `name`
  - `tax_id`
  - `email`
  - `phone`
  - `is_active`
- `core.supplier_invoice`
  - `id`
  - `supplier_id`
  - `business_unit_id`
  - `invoice_no`
  - `invoice_date`
  - `due_date`
  - `net_amount`
  - `gross_amount`
  - `currency`
  - `status`
  - `document_path`

## 7. Mi kerüljön későbbre

Az alábbiakat nem érdemes az első migrationökbe beletenni:
- teljes production struktúra
- teljes events struktúra
- weather és correlation analytics táblák
- purchase order részletes workflow
- inventory snapshot és leltár részletes modell
- audit log és finom meta táblák

Miért:
- ezek növelik a domain-kockázatot
- több iteráció után lehet megbízhatóbban modellezni őket

## 8. Indexelési és kulcsstratégia

MVP-ben ajánlott:
- minden elsődleges kulcs `UUID` vagy egységes surrogate key
- egyedi index:
  - `auth.user.email`
  - `auth.role.code`
  - `auth.permission.code`
  - `core.business_unit.code`
  - `core.product.sku` üzleti egységen belül, ha stabil
- idegen kulcs indexek:
  - `business_unit_id`
  - `location_id`
  - `category_id`
  - `warehouse_id`
  - `inventory_item_id`
  - `supplier_id`
- idő alapú indexek:
  - `occurred_at`
  - `invoice_date`
  - `started_at`

## 9. Seed és reference data stratégia

Az első körben érdemes seedelni:
- alap role-ok: `admin`, `manager`, `analyst`
- alap business unit rekordok: `gourmand`, `flow`
- alap unit of measure rekordok

Nem kell első körben migrationnel seedelni:
- kategóriák
- termékek
- beszállítók
- receptek
- események

Ezek inkább admin felületről vagy importból kerüljenek be.

## 10. Kockázatok és migration anti-patternök

Kerülendő:
- túl nagy, mindent egyszerre létrehozó migration
- production és inventory mély összekötése túl korán
- analytics táblák túl korai véglegesítése
- olyan constraint-ek, amelyekről még nincs stabil üzleti döntés

Ajánlott:
- rövid, jól visszagörgethető revisionök
- minden revision után gyors smoke ellenőrzés
- migration névben a modul és cél egyértelmű jelölése

## 11. Ajánlott következő lépés

E dokumentum után a legjobb következő technikai lépés:
- az első 7 Alembic revision backlogjának konkrét kidolgozása
- a hozzájuk tartozó ORM modellek első verziójának megtervezése
- a `core master data` és `identity` API contract rögzítése
