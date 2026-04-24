Szia, a mellékgépen a munka két nagy irányban haladt:

Procurement posting foundation

új migration: 015_inventory_movement_source_ref
core.inventory_movement kapott source_type / source_id mezőket
új endpoint: POST /api/v1/procurement/purchase-invoices/{purchase_invoice_id}/post
posting létrehoz:
supplier_invoice finance outflow transactiont
invoice line alapú inventory purchase movementeket
frontend Purchase Invoices oldalon Post action és posting status van
Business Dashboard v1 + drill-down

új endpointok:
GET /api/v1/analytics/dashboard
GET /api/v1/analytics/dashboard/categories
GET /api/v1/analytics/dashboard/products
GET /api/v1/analytics/dashboard/expenses
scope-ok: overall, flow, gourmand
period presetek: today, week, month, last_30_days, year, custom
frontend Dashboard már nem sample, hanem valós business dashboard v1
drill-down v1:
category -> product rows
expense type -> transaction rows
Főgépen első lépések:

cd D:\BizTracker-v1\backend
alembic upgrade head
python -m pytest tests\integration\test_procurement_purchase_invoice_posting_api.py tests\integration\test_procurement_purchase_invoices_api.py tests\integration\test_inventory_movement_api.py
Utána a legfontosabb nyitott feladat: analytics dashboard integration testek írása/futtatása valós DB-vel. Mivel a mellékgépen nem volt local DB, a dashboard read-model DB-validáció még nincs meg.

Prioritás szerint én ezt csinálnám a főgépen:

alembic upgrade head
procurement posting integration tesztek futtatása és javítása, ha kell
analytics dashboard integration tesztek:
GET /analytics/dashboard
scope szűrés: overall, flow, gourmand
period presetek, különösen year vs last_30_days
category/product import-derived bontás
expense financial_actual bontás
POS fixture bővítése opcionális category_name mezővel
dashboard következő drill-down mélység:
product -> source POS rows
expense transaction -> source invoice / source record
Dokumentáció szinten most elég jó a helyzet. A fontos fájlok:

docs/DATABASE_SYNC_NOTES.md
docs/DASHBOARD_DIRECTION.md
docs/CURRENT_STATUS.md
docs/ROADMAP.md
Amit még érdemes egységesíteni később:

a régi dokumentumokban néhol még “dashboard sample/reference” szóhasználat lehet; ezt fokozatosan cserélni kell “Business Dashboard v1”-re
a CURRENT_STATUS.md és ROADMAP.md legyen mindig a valós állapot forrása
ha a főgépes DB-validáció megvan, a DATABASE_SYNC_NOTES.md-ben jelölni kell, hogy a 015 migration lefutott és mely tesztek zöldek
Röviden: ne új modult kezdj, előbb validáld a procurement postingot és a dashboard read-modelt valós DB-n. Ez a legfontosabb fonál.
