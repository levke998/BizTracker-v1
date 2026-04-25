# Projektleírás

Ez a dokumentum a két családi vállalkozás számára tervezett belső üzleti webalkalmazás technikai kiinduló terve. A cél egy bővíthető, karbantartható alap lefektetése, amelyre a későbbi implementáció biztonsággal építhető.

Érintett vállalkozások:
- `Gourmand Sütőház és Kézműves Cukrászat`
- `Flow Music Club`

## 1. Projekt céljának összefoglalása

A cél egy belső üzleti menedzsment rendszer, amely:
- közös platformon kezeli a `Gourmand` és a `Flow Music Club` működését,
- üzletenként külön és összesítve is tud riportolni,
- nem csak dashboard, hanem operatív rendszer is,
- támogatja az import alapú indulást (`CSV/Excel`), később API integrációval,
- elkülöníti az `operatív` és az `analitikai` funkciókat.

Explicit feltételezések:
- egy közös belső felhasználói és jogosultsági rendszer lesz,
- a rendszer nem első körben váltja le a kasszát, hanem abból adatot vesz át,
- számlázás és jogi megfelelőség első körben nem teljes ERP-szinten cél, hanem nyilvántartás és elemzés,
- egy közös kódbázis kezeli a két vállalkozást `business unit` alapon.

## 2. Funkcionális modulok listája

### Közös operatív modulok
- hitelesítés és jogosultságkezelés
- törzsadatok: üzletek, telephelyek, kategóriák, partnerek, mértékegységek
- pénzügy: bevételek, kiadások, költséghelyek, fizetési módok
- készletkezelés: raktárak, készletszintek, mozgások, leltár
- beszerzés: beszállítók, beszerzések, beérkező számlák
- import modul: CSV/Excel és később API connectorok
- riporting és export

### Gourmand-specifikus operatív modulok
- alapanyagok
- receptek és receptverziók
- gyártott termékek
- gyártási tételek / batch-ek
- önköltségszámítás
- selejt és veszteség kezelés

### Flow-specifikus operatív modulok
- események / koncertek
- fellépők / zenészek
- jegybevétel
- bárbevétel
- eseményköltségek és elszámolás

### Analitikai modulok
- időszaki teljesítmény és trendek
- üzletek összehasonlítása
- termék- és kategóriaelemzés
- időjárás hatás elemzés a cukrászdára
- esemény hatás elemzés a Flow-ra
- historikus riportok
- később predikció és ajánlás

## 3. Domain modellek és üzleti entitások

Javasolt fő entitások:
- `BusinessUnit`: Gourmand vagy Flow
- `Location`: fizikai hely / üzlet / venue
- `User`, `Role`, `Permission`
- `Supplier`, `CustomerGroup` opcionálisan
- `Category`, `Product`, `UnitOfMeasure`
- `InventoryItem`: alapanyag, félkész, késztermék, ital, merch
- `Warehouse`, `StockMovement`, `InventorySnapshot`
- `PurchaseOrder`, `PurchaseReceipt`, `SupplierInvoice`
- `FinancialTransaction`, `Expense`, `Revenue`, `PaymentMethod`
- `ImportedFile`, `ImportBatch`, `ImportRowError`

### Gourmand
- `Recipe`
- `RecipeVersion`
- `RecipeIngredient`
- `ProductionBatch`
- `BatchConsumption`
- `BatchOutput`
- `WasteRecord`

### Flow
- `Event`
- `EventPerformer`
- `Performer`
- `TicketSaleSummary`
- `BarSaleSummary`
- `EventExpense`
- `EventSettlement`

### Analitika
- `DailySalesFact`
- `DailyExpenseFact`
- `ProductPerformanceFact`
- `EventPerformanceFact`
- `WeatherObservation`

Fontos elv: a `Product` és `InventoryItem` ne legyen teljesen ugyanaz. Egy eladható termék és egy raktárkezelt készletelem sokszor átfed, de nem minden esetben ugyanaz a domain-szerepük.

## 4. Adatbázis séma javaslat

Javaslat: egy PostgreSQL, de logikai elkülönítéssel:
- `auth` séma: felhasználók és jogosultságok
- `core` séma: operatív üzleti adatok
- `ingest` séma: importált nyers adatok és naplók
- `analytics` séma: aggregátumok, materialized view-k, riport fact táblák

### Közös táblák

| Tábla | Fő mezők | Kapcsolatok |
|---|---|---|
| `core.business_unit` | `id`, `code`, `name`, `type` | 1:N `location`, `product`, `event` |
| `core.location` | `id`, `business_unit_id`, `name`, `kind` | N:1 `business_unit` |
| `auth.user` | `id`, `email`, `name`, `is_active` | M:N `role` |
| `auth.role` | `id`, `code`, `name` | M:N `permission` |
| `core.category` | `id`, `business_unit_id`, `parent_id`, `name` | önhivatkozás, N:1 `business_unit` |
| `core.product` | `id`, `business_unit_id`, `category_id`, `sku`, `name`, `product_type`, `is_active` | N:1 `category` |
| `core.inventory_item` | `id`, `business_unit_id`, `name`, `item_type`, `uom_id`, `track_stock` | N:1 `uom` |
| `core.warehouse` | `id`, `location_id`, `name` | N:1 `location` |
| `core.stock_movement` | `id`, `warehouse_id`, `inventory_item_id`, `movement_type`, `qty`, `unit_cost`, `occurred_at`, `source_type`, `source_id` | N:1 `warehouse`, N:1 `inventory_item` |
| `core.supplier` | `id`, `business_unit_id`, `name`, `tax_id`, `contact_data` | 1:N `purchase_order`, `supplier_invoice` |
| `core.purchase_order` | `id`, `supplier_id`, `business_unit_id`, `status`, `ordered_at` | 1:N `purchase_order_line` |
| `core.purchase_order_line` | `id`, `purchase_order_id`, `inventory_item_id`, `qty`, `unit_price` | N:1 `purchase_order` |
| `core.supplier_invoice` | `id`, `supplier_id`, `invoice_no`, `invoice_date`, `due_date`, `net_amount`, `gross_amount`, `status` | opcionális link PO-hoz |
| `core.financial_transaction` | `id`, `business_unit_id`, `location_id`, `direction`, `transaction_type`, `amount`, `currency`, `occurred_at`, `source_type`, `source_id` | központi pénzügyi napló |
| `core.sale_summary` | `id`, `business_unit_id`, `location_id`, `sale_date`, `channel`, `gross_amount`, `net_amount`, `transaction_count`, `source_batch_id` | importból töltve |

### Gourmand-specifikus táblák

| Tábla | Fő mezők | Kapcsolatok |
|---|---|---|
| `core.recipe` | `id`, `product_id`, `name` | 1:N `recipe_version` |
| `core.recipe_version` | `id`, `recipe_id`, `version_no`, `is_active`, `valid_from`, `yield_qty` | 1:N `recipe_ingredient` |
| `core.recipe_ingredient` | `id`, `recipe_version_id`, `inventory_item_id`, `qty` | N:1 `inventory_item` |
| `core.production_batch` | `id`, `business_unit_id`, `recipe_version_id`, `planned_qty`, `produced_qty`, `produced_at`, `status` | 1:N fogyasztás/kimenet |
| `core.batch_consumption` | `id`, `production_batch_id`, `inventory_item_id`, `qty`, `unit_cost` | készletcsökkentés alapja |
| `core.batch_output` | `id`, `production_batch_id`, `inventory_item_id`, `qty`, `unit_cost` | készletnövelés alapja |
| `core.waste_record` | `id`, `business_unit_id`, `inventory_item_id`, `qty`, `reason`, `occurred_at` | selejt elemzéshez |

### Flow-specifikus táblák

| Tábla | Fő mezők | Kapcsolatok |
|---|---|---|
| `core.event` | `id`, `business_unit_id`, `location_id`, `title`, `event_type`, `start_at`, `end_at`, `status` | 1:N performer, bevétel, költség |
| `core.performer` | `id`, `name`, `type`, `contact_data` | M:N `event` |
| `core.event_performer` | `id`, `event_id`, `performer_id`, `fee_type`, `fee_amount` | kapcsolótábla |
| `core.ticket_sale_summary` | `id`, `event_id`, `tickets_sold`, `gross_amount`, `net_amount` | N:1 `event` |
| `core.bar_sale_summary` | `id`, `event_id`, `gross_amount`, `net_amount`, `transaction_count` | N:1 `event` |
| `core.event_expense` | `id`, `event_id`, `expense_type`, `amount`, `supplier_id` | N:1 `event` |
| `core.event_settlement` | `id`, `event_id`, `total_revenue`, `total_cost`, `profit`, `settled_at` | N:1 `event` |

### Analitikai táblák
- `analytics.daily_business_kpi`
- `analytics.product_sales_fact`
- `analytics.category_sales_fact`
- `analytics.event_performance_fact`
- `analytics.weather_observation`
- `analytics.weather_sales_correlation_snapshot`

Kulcselvek:
- minden fontos operatív rekord kapjon `business_unit_id`-t,
- importált adat mindig visszakövethető legyen `source_batch_id` vagy `source_type/source_id` alapján,
- analitikai adat ne írja felül az operatív igazságot.

## 5. Backend architektúra rétegei és felelősségei

Javaslat: `FastAPI + SQLAlchemy 2 + Alembic`, moduláris monolit clean architecture szemlélettel.

### Rétegek
- `presentation`: FastAPI route-ok, DTO-k, auth, input validation
- `application`: use case-ek, orchestráció, tranzakcióhatár, jogosultsági ellenőrzések
- `domain`: entitások, value objectek, domain service-ek, üzleti szabályok
- `infrastructure`: ORM, repository implementációk, fájlimport, külső API-k, scheduler
- `analytics/read model`: lekérdezés-optimalizált riport service-ek és materialized view frissítés

### Modulok / bounded context-ek
- `identity`
- `master_data`
- `finance`
- `inventory`
- `procurement`
- `production`
- `events`
- `imports`
- `analytics`

### Miért jó ez most
- nem overengineerelt,
- üzleti modulok mentén szétválasztható,
- később egyes modulok külön szolgáltatássá emelhetők, ha tényleg szükséges.

## 6. Frontend modulok és oldalak

Javaslat: `React + TypeScript`, route-alapú modulokkal.

### Közös oldalak
- bejelentkezés
- fő dashboard
- üzletválasztó / összehasonlító nézet
- import center
- pénzügyi tranzakciók
- készlet és raktár
- beszerzések és számlák
- riportok
- admin / jogosultságkezelés

### Gourmand oldalak
- termékek és kategóriák
- alapanyagok
- receptek és receptverziók
- gyártási batch-ek
- selejt / veszteség
- termékprofitabilitás
- időjárás vs forgalom elemzés

### Flow oldalak
- eseménynaptár
- esemény adatlap
- fellépők
- jegybevétel / bárbevétel bontás
- esemény profitabilitás
- esemény-összehasonlító analitika

### UI-szétválasztás
- `Operatív` menü: rögzítés, import, készlet, beszerzés, esemény, gyártás
- `Analitika` menü: KPI, trend, összehasonlítás, korreláció, historikus riportok

## 7. API endpoint javaslatok

### Auth
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `GET /api/v1/me`

### Master data
- `GET /api/v1/business-units`
- `GET /api/v1/locations`
- `GET /api/v1/categories`
- `GET /api/v1/products`
- `POST /api/v1/products`

### Inventory / procurement
- `GET /api/v1/inventory/items`
- `GET /api/v1/inventory/stock-levels`
- `POST /api/v1/inventory/movements`
- `GET /api/v1/procurement/suppliers`
- `POST /api/v1/procurement/purchase-orders`
- `POST /api/v1/procurement/invoices`

### Finance
- `GET /api/v1/finance/transactions`
- `POST /api/v1/finance/transactions`
- `GET /api/v1/finance/kpis`

### Gourmand
- `GET /api/v1/production/recipes`
- `POST /api/v1/production/recipes`
- `POST /api/v1/production/recipe-versions`
- `POST /api/v1/production/batches`
- `GET /api/v1/production/batches`
- `GET /api/v1/production/cost-analysis`

### Flow
- `GET /api/v1/events`
- `POST /api/v1/events`
- `GET /api/v1/events/{id}`
- `POST /api/v1/events/{id}/ticket-sales`
- `POST /api/v1/events/{id}/bar-sales`
- `POST /api/v1/events/{id}/expenses`
- `GET /api/v1/events/{id}/settlement`

### Imports
- `POST /api/v1/imports/files`
- `POST /api/v1/imports/pos-sales`
- `POST /api/v1/imports/supplier-invoices`
- `GET /api/v1/imports/batches`
- `GET /api/v1/imports/batches/{id}/errors`

### Analytics
- `GET /api/v1/analytics/dashboard`
- `GET /api/v1/analytics/business-comparison`
- `GET /api/v1/analytics/products/performance`
- `GET /api/v1/analytics/categories/performance`
- `GET /api/v1/analytics/weather-impact`
- `GET /api/v1/analytics/events/performance`

## 8. MVP scope és későbbi bővítési lehetőségek

### MVP
- auth és role alapú hozzáférés
- két üzlet kezelése egy rendszerben
- CSV/Excel import kasszából
- bevétel/kiadás nyilvántartás
- alap készletkezelés és készletmozgások
- beszállítók és számlák kezelése
- Gourmandnál receptek + receptverziók + batch gyártás alap szinten
- Flow-nál események + jegybevétel + bárbevétel + eseményköltség
- alap dashboardok és időszakos riportok
- üzlet-összehasonlító nézet

### Későbbi bővítés
- automatikus POS API integráció
- időjárási adat automatikus szinkron
- prediktív modellek
- ajánlások: készlet, gyártás, beszerzés, eseménytervezés
- anomália detekció
- forecast termékekre, napi forgalomra, eseménybevételre
- mobile-friendly operatív felületek
- könyvelő / számlázó rendszer integráció

## 9. Milyen részeket érdemes a meglévő demóból megtartani koncepcióként

Megjegyzés: a jelenlegi workspace-ben nem volt elérhető a meglévő demó forrása, ezért itt koncepcionális megtartási javaslat szerepel.

Érdemes megtartani:
- KPI-kártyák és gyors összkép logika
- időszűrés és összehasonlító filterezés
- grafikon-szerkezetek, ha üzletileg már hasznosnak bizonyultak
- drill-down szemlélet: összesített nézetből részletek felé
- dashboard információarchitektúra, ha a felhasználók már megszokták
- dummy adatokkal validált üzleti nézetek mint UX input

Amit valószínűleg nem érdemes egy az egyben megtartani:
- demo-orientált state kezelés
- statikus mock adatmodellek
- dashboard-központú architektúra, ha nincs mögötte operatív domain modell
- túl korai általánosítások a két üzlet között

## 10. Kockázatok, technikai döntések, tradeoffok

### Fő döntések
- `Moduláris monolit` az induláshoz jobb, mint microservice.
- `PostgreSQL` elég operatív és kezdeti analitikai célra is.
- `Import-first` stratégia reálisabb, mint rögtön API-first integráció.

### Fő kockázatok
- a kasszaexportok struktúrája változó lehet
- a két üzlet domainje részben közös, részben erősen eltérő
- recept és készlet logika gyorsan bonyolódhat
- analitikai igények hamar túlmutathatnak a kezdeti OLTP modellen
- adattisztítás és historikus adatminőség kritikus lesz

### Tradeoffok
- ha túl általános modellt építünk, romlik az üzleti érthetőség
- ha túl specifikus modellt építünk, nehezebb lesz a közös riport
- ha túl korán külön analytics warehouse épül, nő a komplexitás
- ha nincs külön operatív és analitikai réteg, később nehéz lesz skálázni

### Ajánlott kompromisszum
- egy közös operatív adatmodell,
- külön `analytics` read model réteg ugyanabban a PostgreSQL-ben,
- később, csak valódi igény esetén külön warehouse.

## Technológiai irány

- backend: `Python`, preferáltan `FastAPI`
- frontend: `React + TypeScript`
- adatbázis: `PostgreSQL`
- architektúra: clean architecture, SOLID, moduláris monolit induláskor

## Továbblépési javaslat

A következő tervezési lépésként érdemes elkészíteni:
- konkrét projektmappaszerkezetet,
- backend modulhatárokat,
- frontend route tree-t,
- első MVP user story-k és use case-ek listáját,
- kezdeti migrációs és importstratégiát.
## Dokumentum szerepe es jelenlegi allapot

Ez a dokumentum az eredeti termek- es domain-vizio. Tovabbra is fontos, mert a hosszu tavu celokat, modulokat es uzleti iranyokat nem hagyjuk el.

Nem ez az aktualis implementacios igazsagforras. A projekt tenyleges, futtathato allapotat es a felkesz/hianyzo reszeket a [CURRENT_STATUS.md](C:\BizTracker\docs\CURRENT_STATUS.md) foglalja ossze.

A kovetkezo fejlesztesi fokuszt a [ROADMAP.md](C:\BizTracker\docs\ROADMAP.md), a dokumentacios rendet pedig a [DOCUMENTATION_STATUS.md](C:\BizTracker\docs\DOCUMENTATION_STATUS.md) vezeti.
