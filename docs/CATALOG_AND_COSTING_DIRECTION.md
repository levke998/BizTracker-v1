# Catalog And Costing Direction

Ez a dokumentum a termek- es alapanyagkatalogus, a receptalapu koltsegmodell, valamint a margin szamitas jelenlegi iranyat foglalja ossze.

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
GET /api/v1/catalog/ingredients
```

Frontend:
- `Catalog - Products`
- `Catalog - Ingredients`

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
- `profit_margin` HUF fo ertek
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

## Kovetkezo implementacios szelet

1. Product write API:
   - create product
   - update sale price
   - update category
   - update sales UOM
   - update direct unit cost

2. Recipe write API:
   - create recipe
   - create new recipe version
   - add/remove ingredient
   - change ingredient quantity
   - recalculate margin immediately

3. Ingredient write API:
   - create inventory item
   - update default unit cost
   - update estimated stock quantity
   - keep manual edit compatible with later supplier invoice updates

4. Estimated stock:
   - POS sale -> recipe consumption estimate
   - do not block sales when estimated stock is zero
   - stock floor should not go below zero in the read model
