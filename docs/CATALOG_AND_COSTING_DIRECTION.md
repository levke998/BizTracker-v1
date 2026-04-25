# Catalog And Costing Direction

Ez a dokumentum a termek- es alapanyagkatalogus, a receptalapu koltsegmodell, valamint a margin szamitas jelenlegi iranyat foglalja ossze.

Kapcsolodo dokumentumok:
- [CURRENT_STATUS.md](C:\BizTracker\docs\CURRENT_STATUS.md)
- [ROADMAP.md](C:\BizTracker\docs\ROADMAP.md)
- [DOCUMENTATION_STATUS.md](C:\BizTracker\docs\DOCUMENTATION_STATUS.md)

## Jelenlegi allapot

Adatbazis alap:
- `core.product.sale_price_gross`
- `core.product.default_unit_cost`
- `core.product.sales_uom_id`
- `core.inventory_item.default_unit_cost`
- `core.inventory_item.estimated_stock_quantity`
- `core.recipe`
- `core.recipe_version`
- `core.recipe_ingredient`

Katalogus API:

```text
GET /api/v1/catalog/products
POST /api/v1/catalog/products
PATCH /api/v1/catalog/products/{product_id}
DELETE /api/v1/catalog/products/{product_id}
GET /api/v1/catalog/ingredients
POST /api/v1/catalog/ingredients
PATCH /api/v1/catalog/ingredients/{inventory_item_id}
DELETE /api/v1/catalog/ingredients/{inventory_item_id}
```

Frontend:
- `Catalog - Products`
- `Catalog - Ingredients`
- termek letrehozas es szerkesztes
- termek archivalas soft delete modon, audit/history megtartassal
- direkt koltseg, eladasi ar, kategoria es sales UOM modositasa
- receptes termeknel uj aktiv receptverzio letrehozasa rugalmas osszetevo listaval
- alapanyag letrehozas es szerkesztes
- alapanyag archivalas soft delete modon, recept es keszlet history megtartassal
- alapanyag koltseg es becsult stock kezi karbantartasa

Fontos mukodesi szabaly:
- a catalog delete jelenleg archivalas (`is_active=false`), nem fizikai torles
- a bootstrap reference data nem archivalhatja a felhasznalo altal letrehozott catalog rekordokat csak azert, mert nincsenek benne a seed catalogban

## Termekkoltseg szabaly

Receptes termek:
- a recept aktiv verziojanak osszetevoi alapjan szamoljuk a teljes receptkoltseget
- az osszetevok koltsege `inventory_item.default_unit_cost`
- g/kg es ml/l atvaltas tamogatott
- az egy eladasi egysegre eso koltseg: recept teljes koltseg / recept hozam

Direkt termek:
- ha nincs recept, a termek `default_unit_cost` erteke a beszerzesi vagy direkt egysegkoltseg
- ilyenek tipikusan uditok, italok, jegyek

Margin:
- `estimated_unit_cost` = receptkoltseg vagy direkt koltseg
- `estimated_margin_amount` = `sale_price_gross - estimated_unit_cost`
- `estimated_margin_percent` = margin / eladasi ar

## Dashboard kapcsolat

A dashboard a POS sorokhoz termekkod alapjan keresi a koltseget:
- `product_id`
- `sku`
- `product_name`

KPI-k:
- `estimated_cogs`
- `profit_margin` HUF fo ertek, vagyis estimated margin profit
- `gross_margin_percent` masodlagos szazalek

Trend chart:
- revenue
- cost
- profit
- estimated COGS
- margin profit

## Mennyisegi modell

A db most mar kepes sales UOM tarolasara termekszinten. Ez fontos, mert nem minden termek darabos:
- edes sutemenyek jellemzoen szelet/db
- fagylalt gomboc/adag
- italok db/palack
- egyes sos termekek kg alapon is mukodhetnek

Nyitott dontes:
- a meglévő seedben mely termekeket kell kg alapu ertekesitesre atallitani
- a `prods.docx` alapjan ehhez meg explicit termekenkenti jovahagyas kell, hogy ne irjunk at vakon darabos termeket kg-ra

## Estimated stock consumption

POS receipt ingestion utan a rendszer becsult stock fogyast szamol:
- receptes termeknel az aktiv receptverzio osszetevoi alapjan
- direkt trackelt kesztermeknel a termek nevet egyezteti inventory itemmel
- csak kompatibilis mertekegysegeknel von le keszletet
- a becsult stock 0 ala nem mehet
- a fogyas nem blokkolja az eladast

Nyitott tovabbfejlesztes:
- a becsult fogyas kulon audit tablaba keruljon, hogy visszakeresheto legyen melyik nyugta melyik alapanyagot csokkentette

## Kovetkezo implementacios szelet

1. Estimated stock audit:
   - POS sale -> recipe consumption audit row
   - receipt/source row level traceability
   - manual correction history

2. POS mapping:
   - external cash-register product code -> BizTracker product
   - SKU and barcode aliases
   - missing mapping quarantine

3. Catalog UX hardening:
   - archive/deactivate decisions
   - larger recipe editor ergonomics
   - duplicate SKU warnings
