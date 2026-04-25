# Dashboard Direction

Ez a dokumentum a BizTracker valodi business dashboard iranyat rogziti. A korabbi frontend dashboard design referencia volt; innen tovabb a dashboard valodi uzleti read model es elemzesi felulet.

Kapcsolodo dokumentumok:
- [BUSINESS_DIRECTION.md](C:\BizTracker\docs\BUSINESS_DIRECTION.md)
- [ACCOUNTING_AND_CONTROLLING_MODEL.md](C:\BizTracker\docs\ACCOUNTING_AND_CONTROLLING_MODEL.md)
- [CURRENT_STATUS.md](C:\BizTracker\docs\CURRENT_STATUS.md)
- [DATABASE_SYNC_NOTES.md](C:\BizTracker\docs\DATABASE_SYNC_NOTES.md)

## 1. Dashboard scope-ok

A dashboard harom fo scope-pal dolgozik:

1. `overall`
   - osszesitett uzleti kep
   - Flow es Gourmand egyutt
   - business owner szintu gyors attekintes

2. `flow`
   - Flow Music Club uzleti kep
   - kesobb event, ticket, bar es performer bontasok

3. `gourmand`
   - Gourmand uzleti kep
   - kesobb category, product, recipe, estimated COGS es weather bontasok

Az `overall` nem kulon domain, hanem a Flow es Gourmand adatok egyesitett nezete.

## 2. Idoszak szemlelet

A dashboard presetek:
- `today`
- `week`
- `month`
- `last_30_days`
- `year`
- `custom`

Fontos pontositas:
- `year` = idei ev eddig, nem fixen peldaul 2026
- `month` = aktualis honap eddig
- `last_30_days` = gordulo 30 nap, nem ugyanaz mint az aktualis honap
- `custom` = explicit `start_date` es `end_date`

## 3. Elso backend contract

Aktualis endpoint:

```text
GET /api/v1/analytics/dashboard
```

Query parameterek:
- `scope`
- `period`
- `business_unit_id` opcionails override
- `start_date` custom idoszakhoz
- `end_date` custom idoszakhoz

Aktualis fo response reszek:
- `kpis`
- `revenue_trend`
- `category_breakdown`
- `top_products`
- `expense_breakdown`
- `notes`

Aktualis KPI-k:
- `revenue`
- `cost`
- `profit`
- `transaction_count`
- `profit_margin`
- `average_basket_value`
- `average_basket_quantity`

Fontos cost pontositas:
- a `cost` jelenleg tenylegesen postolt penzugyi kiadas az adott idoszakban
- ha egy napon nincs postolt kiadas, akkor arra a napra a cost `0`
- ez nem jelenti azt, hogy az adott napi eladasnak nincs estimated COGS koltsege
- estimated COGS kesobb a recipe / consumption / FIFO iranybol kerul be

Fontos margin pontositas:
- a `profit_margin` jelenleg `profit / revenue * 100`
- a `profit` most `revenue - posted financial outflow`
- ez actual controlling margin, nem teljes szamviteli vagy FIFO COGS margin

## 3/A. Drill-down endpointok v1

Aktualis drill-down endpointok:

```text
GET /api/v1/analytics/dashboard/categories
GET /api/v1/analytics/dashboard/products
GET /api/v1/analytics/dashboard/product-rows
GET /api/v1/analytics/dashboard/expenses
GET /api/v1/analytics/dashboard/expense-source
GET /api/v1/analytics/dashboard/basket-pairs
GET /api/v1/analytics/dashboard/basket-pair-receipts
```

Kozos query parameterek:
- `scope`
- `period`
- `business_unit_id` opcionails override
- `start_date` custom idoszakhoz
- `end_date` custom idoszakhoz

Specialis query parameterek:
- `products`: `category_name`
- `product-rows`: `product_name`, `category_name`, `limit`
- `expenses`: `transaction_type`
- `expense-source`: `transaction_id`
- `basket-pairs`: `limit`
- `basket-pair-receipts`: `product_a`, `product_b`, `limit`

Jelenlegi drill-down jelentese:
- category -> product detail rows
- product -> source POS import rows
- expense type -> financial transaction rows
- expense transaction -> supplier invoice source record and invoice lines
- receipt groups -> frequently co-purchased product pairs
- product pair -> source receipt baskets and receipt POS rows

Kovetkezo drill-down cel:
- receipt detail -> future basket-level behavior and recommendation analysis

Kosar KPI-k:
- `average_basket_value` = POS import sorok `receipt_no` csoportjai alapjan szamolt atlagos kosarertek
- `average_basket_quantity` = POS import sorok `receipt_no` csoportjai alapjan szamolt atlagos termekmennyiseg
- nepszeru egyutt vasarolt termekek a `basket-pairs` endpointon erhetok el

Kosarpar modell:
- forras: parsed `pos_sales` import sorok
- csoportositas: `receipt_no`
- egy kosarban szereplo kulonbozo termekekbol termekparok kepzodnek
- `basket_count` = hany kosarban fordult elo a termekpar
- `total_gross_amount` = a parhoz tartozo termeksorok bruttó osszege az erintett kosarakban
- ez import-derived elemzes, nem domain mapping es nem predikcio

Kosar source detail:
- `basket-pair-receipts` visszaadja azokat a receipt-eket, amelyekben a kivalasztott termekpar egyutt szerepelt
- minden receipt alatt latszanak a teljes POS sorok
- ez segit megerteni, hogy egy par milyen nagyobb kosarkontextusban fordul elo

## 4. Data lineage

Az elso dashboard read model tudatosan kulon kezeli az adatforrasokat:

- `financial_actual`
  - `core.financial_transaction`
  - revenue, cost, profit, expense breakdown

- `import_derived`
  - parsed `pos_sales` import rows
  - product es category breakdown

- `derived_actual`
  - financial actualokbol szamolt profit

Ez azert fontos, mert nem keverjuk ossze a tenyleges penzugyi adatot es az import staging sorokbol szarmaztatott termekbontast.

## 5. Drill-down cel

A vegcel:

```text
scope -> period -> KPI -> category -> product -> source row / transaction
```

Pelda revenue oldalon:

```text
Revenue -> Sweet category -> Dobos cake -> POS import rows / finance transactions
```

Pelda cost oldalon:

```text
Cost -> supplier_invoice -> invoice -> invoice lines -> inventory movements
```

Aktualis cost oldali drill-down:

```text
Expense breakdown -> supplier_invoice transaction -> supplier invoice header -> invoice lines
```

Az elso implementacio meg aggregalt read model, de a response struktura mar a kesobbi drill-down iranyt kesziti elo.

## 6. Kiadások szerepe

A kiadasok kulon fontos dashboard elemkent jelennek meg:
- expense breakdown
- cost KPI
- profit szamitas bemenete

Kovetkezo bovites:
- supplier szerinti bontas
- invoice szerinti drill-down
- cost center / expense category modell
- procurement posting validalasa utan pontosabb cost oldali dashboard

## 7. Kovetkezo fejlesztesek

Javasolt sorrend:

1. fo gepen DB migration es procurement posting tesztek futtatasa
2. fo gepen analytics dashboard endpoint integration test
3. category_name mezovel bovitheto POS CSV fixture
4. receipt detail -> basket-level behavior kovetkezo elemzesi modell
5. Flow event dashboard szelet
6. Gourmand product/category dashboard szelet
