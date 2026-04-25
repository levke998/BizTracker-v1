# Database Sync Notes

Ez a dokumentum azt rogziti, hogy a local database nem ezen a PC-n van, hanem a fo fejlesztoi gepen. Emiatt minden adatbazis-valtozast Alembic migrationkent kell kezelni, es munkakezdeskor a fo gepen ezekkel kell kezdeni.

## Fo gepen kovetendo munkakezdes

Backend konyvtarbol:

```powershell
cd D:\git\BizTracker-v1\backend
alembic upgrade head
```

Ha a backend `.env` nincs betoltve automatikusan, elobb a fo gepen be kell allitani a `DATABASE_URL` erteket a lokalis PostgreSQL adatbazisra.

## Jelenlegi adatbazis allapot

### `018_pos_sale_dedupe_key`

Fajl:
- `backend/migrations/versions/20260425_018_pos_sale_dedupe_key.py`

Cel:
- ugyanaz az eladas ne tudjon duplazodni API es CSV forras kozott
- azonos CSV export tobbszori feltoltese ne hozzon letre uj penzugyi tranzakciokat
- kasszakapcsolat kiesese es CSV fallback biztonsagosan egy pipeline-ba keruljon

Valtozas:
- `core.financial_transaction.dedupe_key`
- `ix_core_financial_transaction_dedupe_key` unique index

Kapcsolodo workflow:
- `POST /api/v1/pos-ingestion/receipts`
- `POST /api/v1/imports/files`
- `POST /api/v1/imports/batches/{batch_id}/parse`
- `POST /api/v1/imports/batches/{batch_id}/map/financial-transactions`
- a dedupe kulcs business unit, date, receipt_no, product_name, quantity es gross_amount alapon epul
- csak a nem duplikalt POS sorok hoznak letre finance tranzakciot es becsult stock fogyast

### `017_core_costing_foundation`

Fajl:
- `backend/migrations/versions/20260424_017_core_costing_foundation.py`

Cel:
- a termekek ertekesitesi mertekegysege kulon tarolhato legyen
- az alapanyagokhoz es keszletelemekhez legyen torzs szintu beszerzesi egysegkoltseg
- legyen hely a becsult keszlet mennyisegnek, amelyet kesobb szamlafeltoltes es POS fogyas becsles frissithet
- a dashboard a receptbol vagy direkt termekkoltsegbol tudjon becsult COGS es margin-profit erteket szamolni

Valtozas:
- `core.inventory_item.default_unit_cost`
- `core.inventory_item.estimated_stock_quantity`
- `core.product.sales_uom_id`

Kapcsolodo workflow:
- `python -m scripts.bootstrap_reference_data`
- frissiti a prods.docx alapu arakat, sales UOM adatokat es alapanyag koltsegeket
- 72 keszletelemhez realis becsult `estimated_stock_quantity` induloadatot ad
- torli a zavaro `Reusable Demo Item%` keszletelemeket, ha nincs rajtuk movement referencia
- a demo POS a `POST /api/v1/pos-ingestion/receipts` boundaryn keresztul kuld nyugtat
- a dashboard `estimated_cogs`, HUF `profit_margin` es `% gross_margin_percent` KPI-ket szamol
- POS receipt ingestion utan a becsult stock recept vagy direkt trackelt kesztermek alapjan csokken, 0 also korlattal
- katalogus endpointok:
  - `GET /api/v1/catalog/products`
  - `GET /api/v1/catalog/ingredients`

### `016_product_recipe_base`

Fajl:
- `backend/migrations/versions/20260424_016_core_product_recipe_foundation.py`

Cel:
- a demo kassza elokeszitesehez a termekek taroljanak aktualis brutto arat es opcionalis alap egysegkoltseget
- a Gourmand recept/BOM alap bekeruljon normalizalt tablakba
- a theoretical stock kesobbi sales -> recipe -> estimated consumption logikaja ne szoveges seed adatokbol induljon

Valtozas:
- `core.product.sale_price_gross`
- `core.product.default_unit_cost`
- `core.product.currency`
- `core.recipe`
- `core.recipe_version`
- `core.recipe_ingredient`

Kapcsolodo workflow:
- `python -m scripts.bootstrap_reference_data`
- seedeli a `prods.docx` alapjan a Gourmand sutemeny/torta/fagylalt termekeket es recepteket
- seedeli a Flow ital es jegy termekeket
- torli a korabbi demo import batch-eket es dummy beszallitokat
- inaktivalja a kataloguson kivuli regi demo termek/keszletelem rekordokat

### `015_inventory_movement_source_ref`

Fajl:
- `backend/migrations/versions/20260424_015_core_inventory_movement_source_ref.py`

Cel:
- az inventory movement log visszakovethetove valik forrasrekordra
- a supplier invoice line -> inventory movement kapcsolat duplikacio ellen vedett lesz
- ez szukseges a purchase invoice posting flow-hoz

Valtozas:
- `core.inventory_movement.source_type`
- `core.inventory_movement.source_id`
- `ix_core_inventory_movement_source_ref`
- `uq_core_inventory_movement_source_ref`

Kapcsolodo workflow:
- `POST /api/v1/procurement/purchase-invoices/{purchase_invoice_id}/post`
- penzugyi `supplier_invoice` outflow tranzakciot hoz letre
- inventory itemhez kotott szamlasorokbol `purchase` movementeket hoz letre
- purchase invoice list response jelzi a posting allapotot:
  - `is_posted`
  - `posted_to_finance`
  - `posted_inventory_movement_count`

## 2026-04-24 fo gepes validacio allapota

Ezen a gepen a `018_pos_sale_dedupe_key` migration sikeresen lefutott. A kapcsolodo procurement posting validacio, Business Dashboard v1 read-model integration validacio es a teljes backend integration csomag is zold.

Lefutott ellenorzesek:

```powershell
cd C:\BizTracker\backend
python -m alembic upgrade head
python -m alembic current
python -m pytest C:\BizTracker\backend\tests\integration\test_procurement_purchase_invoice_posting_api.py C:\BizTracker\backend\tests\integration\test_procurement_purchase_invoices_api.py C:\BizTracker\backend\tests\integration\test_inventory_movement_api.py -q
python -m pytest C:\BizTracker\backend\tests\integration\test_analytics_dashboard_api.py -q
python -m pytest C:\BizTracker\backend\tests\integration\test_procurement_purchase_invoice_posting_api.py C:\BizTracker\backend\tests\integration\test_procurement_purchase_invoices_api.py C:\BizTracker\backend\tests\integration\test_inventory_movement_api.py C:\BizTracker\backend\tests\integration\test_analytics_dashboard_api.py -q
python -m pytest C:\BizTracker\backend\tests\integration -q
```

Eredmeny:
- Alembic head: `018_pos_sale_dedupe_key`
- procurement posting + inventory movement tesztek: `14 passed`
- analytics dashboard tesztek: `9 passed`
- kombinált validacios csomag: `23 passed`
- frontend production build: sikeres
- katalogus smoke check: `/catalog/products` es `/catalog/ingredients` 200 OK
- catalog write integration teszt: `backend/tests/integration/test_catalog_api.py`
- teljes backend integration csomag: `88 passed`
- POS CSV/API dedupe celtesztek: `16 passed`

Megjegyzes:
- ezen a gepen az `alembic_version.version_num` oszlop kezdetben tul rovid volt a `015_inventory_movement_source_ref` revision azonositohoz
- lokalis DB metadata fix kellett:
  - `ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(64)`
- ez nem alkalmazaslogikai hiba volt, hanem lokalis adatbazis metadata szinkron problema

## Kovetkezo fo gepes ellenorzesek

Procurement posting es Business Dashboard v1 oldalon a fo DB-validacio megtortent.

Munkakezdeskor tovabbra is javasolt:

```powershell
cd C:\BizTracker\backend
python -m alembic current
```

Nyitott prioritas innen tovabb:
- dashboard kovetkezo drill-down melyseg
- basket-level behavior elso read modellje
- identity/auth MVP elokeszitese

## DB-t nem modosito, de fo gepen ellenorzendo dashboard munka

Aktualis uj endpoint:

```text
GET /api/v1/analytics/dashboard
GET /api/v1/analytics/dashboard/categories
GET /api/v1/analytics/dashboard/products
GET /api/v1/analytics/dashboard/product-rows
GET /api/v1/analytics/dashboard/expenses
GET /api/v1/analytics/dashboard/expense-source
GET /api/v1/analytics/dashboard/basket-pairs
GET /api/v1/analytics/dashboard/basket-pair-receipts
```

Ez nem igenyel uj migrationt, mert meglevo tablakbol olvas:
- `core.financial_transaction`
- `ingest.import_batch`
- `ingest.import_row`
- `core.business_unit`

Dashboardhoz mar van DB-s integration teszt:
- `backend/tests/integration/test_analytics_dashboard_api.py`

Lefedett validacio:
- `GET /api/v1/analytics/dashboard`
- scope szures: `overall`, `flow`, `gourmand`
- period preset validacio: `year`, `last_30_days`
- category -> product import-derived bontas
- product -> source POS rows bontas
- expense financial_actual bontas
- expense transaction -> supplier invoice source bontas
- basket-pair import-derived bontas
- basket-pair -> source receipt POS sorok bontas

## Fejlesztesi szabaly innen tovabb

- adatbazis-valtozas csak migrationnel keruljon be
- minden uj migration keruljon be ebbe a dokumentumba rovid leirassal
- fo gepen munkakezdeskor elso lepes az `alembic upgrade head`
- fo gepen ezutan futtathatok az integration tesztek
- a `CURRENT_STATUS.md` es a `ROADMAP.md` mar a tenyleges termekallapot forrasai
