# Database Sync Notes

Ez a dokumentum azt rogziti, hogy a local database nem ezen a PC-n van, hanem a fo fejlesztoi gepen. Emiatt minden adatbazis-valtozast Alembic migrationkent kell kezelni, es munkakezdeskor a fo gepen ezekkel kell kezdeni.

## Fo gepen kovetendo munkakezdes

Backend konyvtarbol:

```powershell
cd D:\git\BizTracker-v1\backend
alembic upgrade head
```

Ha a backend `.env` nincs betoltve automatikusan, elobb a fo gepen be kell allitani a `DATABASE_URL` erteket a lokalis PostgreSQL adatbazisra.

## Jelenlegi pending adatbazis-valtozas

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

Kapcsolodo uj workflow:
- `POST /api/v1/procurement/purchase-invoices/{purchase_invoice_id}/post`
- penzugyi `supplier_invoice` outflow tranzakciot hoz letre
- inventory itemhez kotott szamlasorokbol `purchase` movementeket hoz letre
- purchase invoice list response jelzi a posting allapotot:
  - `is_posted`
  - `posted_to_finance`
  - `posted_inventory_movement_count`

## Fo gepen potolando ellenorzesek

Mivel ezen a PC-n nincs local database, a DB-fuggo ellenorzesek a fo gepen futtatandok.

Javasolt sorrend:

```powershell
cd D:\git\BizTracker-v1\backend
alembic upgrade head
python -m pytest tests\integration\test_procurement_purchase_invoice_posting_api.py tests\integration\test_procurement_purchase_invoices_api.py tests\integration\test_inventory_movement_api.py
```

Ezek ellenorzik:
- supplier invoice posting letrehozza a finance transactiont
- inventory itemhez kotott szamlasorbol purchase movement lesz
- ugyanaz a supplier invoice nem postolhato ketszer
- purchase invoice lista visszaadja a posting allapotot
- inventory movement manual create flow tovabbra is mukodik

## DB-t nem modosito, de fo gepen ellenorzendo dashboard munka

Aktualis uj endpoint:

```text
GET /api/v1/analytics/dashboard
GET /api/v1/analytics/dashboard/categories
GET /api/v1/analytics/dashboard/products
GET /api/v1/analytics/dashboard/expenses
```

Ez nem igenyel uj migrationt, mert meglevo tablakbol olvas:
- `core.financial_transaction`
- `ingest.import_batch`
- `ingest.import_row`
- `core.business_unit`

Fo gepen javasolt ellenorzes a migration utan:

```powershell
python -m pytest tests\integration\test_procurement_purchase_invoice_posting_api.py tests\integration\test_procurement_purchase_invoices_api.py tests\integration\test_inventory_movement_api.py
```

Dashboardhoz meg nincs DB-s integration test. Kovetkezo fo gepes feladat:
- analytics dashboard integration test irasa/futtatasa
- POS CSV fixture bovites opcionails `category_name` mezovel
- ellenorizni, hogy a dashboard scope-ok (`overall`, `flow`, `gourmand`) valos adatokon helyesen szurnek
- ellenorizni, hogy a drill-down endpointok category/product/expense szinten valos adatokon mukodnek

## Fejlesztesi szabaly innen tovabb

- adatbazis-valtozas csak migrationnel keruljon be
- minden uj migration keruljon be ebbe a dokumentumba rovid leirassal
- DB-fuggo tesztet ezen a PC-n nem tekintunk kotelezonek
- fo gepen munkakezdeskor elso lepes az `alembic upgrade head`
- fo gepen ezutan futtathatok az integration tesztek
