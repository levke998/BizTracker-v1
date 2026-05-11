# BizTracker rovid szakmai leiras vedeshez

## Mi az alkalmazas?

A BizTracker egy belso uzleti elemzo es controlling alkalmazas a Gourmand es a Flow Music Club mukodesenek kovetesere. Nem konyvelesi program es nem realtime kasszarendszer, hanem forrasadatig visszakovetheto dontestamogato rendszer. A fo cel az, hogy a POS CSV exportokbol, beszerzesi szamlakbol, receptekbol, keszletmozgasokbol, event adatokbol es idojarasi adatokbol uzleti KPI-ket, kockazati jelzeseket es munkalistakat keszitsen.

Az alkalmazas egyik legfontosabb szakmai alapelve az `actual`, `estimated` es `derived` adatok szetvalasztasa:

- `actual`: rogzitett tenyadat, peldaul POS brutto bevetel, beszerzesi szamla, inventory movement.
- `estimated`: receptbol vagy szabalybol szamolt becsles, peldaul alapanyag-fogyas vagy teoretikus keszlet.
- `derived`: actual es estimated adatokbol kepzett mutato, peldaul margin, estimated COGS vagy variance statusz.

Ez azert fontos, mert a rendszer nem allitja tenyadatnak azt, amit csak becsulni tud.

## Technikai felepites

A rendszer modularis monolit. A backend FastAPI, SQLAlchemy 2 es Alembic alapon keszult, a frontend React, TypeScript, Vite es TanStack Query technologiakat hasznal. Az alkalmazas modulokra bontva mukodik: `imports`, `pos_ingestion`, `finance`, `catalog`, `production`, `inventory`, `procurement`, `events`, `weather`, `analytics`, `identity` es `master_data`.

A backend clean architecture iranyt kovet:

```text
presentation -> application -> domain -> infrastructure
```

A presentation reteg HTTP API-t es request/response semakat kezel. Az application reteg use case-eket vezenyel. A domain tartalmazza az uzleti fogalmakat es szabalyokat. Az infrastructure retegben vannak az ORM modellek es SQLAlchemy repository implementaciok.

## Adatpipeline

A rendszer fo adatbeviteli iranya CSV-first:

```text
raw fajl -> import_file -> import_batch -> import_row -> mapping -> finance/inventory/analytics
```

A POS/kasszaadat nem realtime API-bol jon, hanem ellenorizheto exportbol. Egy POS import csomag osszesito es teteles CSV-bol all. Az osszesito adja a kategoriakat, a teteles fajl a valos eladasi sorokat es idopontokat. A parser ellenorzi, hogy az osszesito es teteles fajlok idoszaka osszhangban van-e.

## Fo szamitasok

### POS bevetel es deduplikacio

Egy parsed POS sorbol penzugyi tranzakcio keszul:

```text
amount = gross_amount
direction = inflow
transaction_type = pos_sale
currency = HUF
```

A duplazas ellen dedupe kulcs keszul:

```text
business_unit_id + date + receipt_no + product_name + quantity + gross_amount + source_line_key
```

A mennyiseg 0.001, a penzosszeg 0.01 pontossagra normalizalodik, majd SHA-256 hash keszul. Igy ugyanaz a CSV ujrafeltoltve nem hoz letre uj bevetelt.

### Recept es onkoltseg

A recept a production modulban van. Egy termekhez aktiv receptverzio tartozhat, amely inventory item osszetevokbol all. A receptkoltseg:

```text
ingredient_cost = converted_quantity * inventory_item.default_unit_cost
known_total_cost = ismert osszetevok koltsegeinek osszege
total_cost = known_total_cost, ha nincs hianyzo koltseg
unit_cost = total_cost / recipe_yield_quantity
```

A rendszer g/kg es ml/l konverziot kezel. Ha egy osszetevo koltsege hianyzik, nem szamol hamis teljes onkoltseget, hanem `missing_cost` allapotot ad. Ha nincs recept, `missing_recipe`; ha van recept, de nincs osszetevo, `empty_recipe`; ha a keszlet nem elegendo vagy hianyzik, `missing_stock`; ha minden rendben van, `ready`.

### Estimated consumption

POS eladas utan a rendszer megprobalja a sort belso termekhez kotni:

```text
product_id -> mapped POS alias -> SKU -> product_name
```

Ha van aktiv recept, akkor az alapanyag-fogyas:

```text
estimated_usage = recipe_ingredient.quantity * sold_quantity / recipe_yield_quantity
```

Ezutan mertekegyseg-konverzio tortenik, majd csokken a becsult keszlet:

```text
quantity_after = max(0, quantity_before - converted_quantity)
```

Minden becsult fogyas audit sort hoz letre, amely megorzi a source type-ot, source id-t, dedupe key-t, nyugtaszamot, receptverziot, mennyiseget es elotte/utana keszletet.

### Actual es teoretikus keszlet

Az actual keszlet inventory movementekbol epul:

```text
current_quantity = purchase + initial_stock + adjustment - waste
```

A teoretikus keszlet az estimated stock mezobol jon. A variance:

```text
variance_quantity = actual_quantity - theoretical_quantity
actual_stock_value = actual_quantity * default_unit_cost
theoretical_stock_value = theoretical_quantity * default_unit_cost
variance_stock_value = variance_quantity * default_unit_cost
```

Ha hianyzik a koltseg vagy a teoretikus mennyiseg, a rendszer statuszt ad, nem kitalalt erteket. Statuszok: `missing_theoretical_stock`, `missing_cost`, `ok`, `shortage_risk`, `surplus_or_unreviewed`.

### Inventory variance es fizikai szamolas

Fizikai keszletszamolasnal:

```text
adjustment_quantity = counted_quantity - current_quantity
```

Pozitiv elteres `adjustment`, negativ elteres `waste` movement. A reason code jelzi az okot: selejt, tores, lopasgyanu, recept hiba, mapping hiba, kimaradt szamla stb.

A HUF becsles:

```text
estimated_shortage_value = waste_quantity * default_unit_cost
estimated_surplus_value = adjustment_quantity * default_unit_cost
estimated_net_value_delta = surplus_value - shortage_value
```

Az aktualis periodus az elozo azonos hosszu periodussal hasonlithato ossze. A dontesi statusz lehet `stable`, `watch`, `worsening`, `critical`, `improving` vagy `missing_cost`, uzletenkent mentett kuszobok alapjan.

### AFA es beszerzesi szamla

Penzugyi szamitasnal `Decimal` tipust hasznalunk, nem `float`-ot. Az AFA szamitas:

```text
factor = 1 + rate_percent / 100
net = gross / factor
gross = net * factor
vat = gross - net
```

A `VatCalculator` bruttobol vagy nettobol szamol, illetve a szamlan szereplo netto/AFA/brutto ertekeket egyezteti. Eltérésnel `review_needed` statuszt ad.

A beszerzesi szamla posting hatasa:

```text
finance outflow = invoice.gross_total
inventory purchase movement = invoice line quantity
unit_cost = line_net_amount / quantity
```

Postingkor az inventory item aktualis default koltsege is frissul a szamlasor netto egysegarabol, de regebbi szamla nem irhatja felul a frissebb costot.

### Dashboard

A dashboard backend read modelbol keszul:

```text
revenue = sum(inflow transaction amount)
cost = sum(outflow transaction amount)
profit = revenue - cost
estimated_cogs = sum(product_unit_cost * sold_quantity)
margin_profit = revenue - estimated_cogs
gross_margin_percent = margin_profit / revenue * 100
```

A product unit cost receptes termeknel aktiv receptbol, egyebkent `product.default_unit_cost` mezobol jon. A kosarmutatok receipt number szerint csoportositott POS sorokbol keszulnek:

```text
average_basket_value = total basket gross amount / basket count
average_basket_quantity = total basket quantity / basket count
```

A dashboard minden fontos KPI-n jeloli, hogy az osszeg brutto/netto/mixed es actual/derived eredetu-e.
POS bevetelnel a brutto kassza actual marad az igazsagforras, a netto/AFA bontas pedig termek AFA torzsadatbol szamolt derived adat. A dashboard kulon `vat_readiness` jelzest ad arra, hogy az adott idoszak POS forgalmanak mekkora reszehez van AFA-kulcs lefedettseg. Termek szinten a margin mar netto bevetelbol es netto COGS-bol szamolodik, kulon `margin_status` jelzessel, hogy hianyzo AFA vagy hianyzo koltseg ne torzitson.

## Mi van keszen?

Kesz a backend/frontend alap, auth MVP, CSV import pipeline, POS dedupe, POS mapping munkalista, termek- es alapanyagkatalogus, recept readiness, estimated COGS, inventory actual es theoretical stock, fizikai keszletszamolas, variance elemzes, beszerzesi szamla review es posting elso szelete, dashboard v1 POS AFA readiness jelzessel, weather/forecast cache, valamint Flow event es ticket actual alap.

## SOLID es Clean Code

A rendszerben a felelossegek szet vannak valasztva. A `VatCalculator` csak AFA-t szamol, a POS mapping command csak tranzakciot kepez, a POS inventory service csak becsult fogyast kezel, a production repository csak recept read modelt epit. Ez a Single Responsibility elv gyakorlati megvalositasa.

A use case-ek repository contractokon keresztul dolgoznak, nem kozvetlenul ORM reszletekkel. Ez a Dependency Inversion elvet koveti. A domain nem ismeri az adatbazis implementaciot. Az alkalmazas hianyos adatnal nem omlik ossze, hanem uzleti allapotot ad: `missing_cost`, `missing_recipe`, `review_needed`, `missing_theoretical_stock`.

Clean Code szempontbol fontos meg a source lineage, az idempotens POS posting, a Decimal alapu penzugyi szamitas, a nem kodba egetett variance kuszob, valamint az, hogy a frontend megjelenit, de a meghatarozo uzleti szamitasok backend read modelben tortennek.

## Jovo

A kovetkezo teruletek: tomeges POS alias review, PDF OCR/adatkinyeres, teljesebb netto/brutto/AFA riportolas, fejlettebb receptverzio es publikacio, inventory controlling melyebb ok- es item-szintu javaslatok, Flow event elszamolas melyitese, Gourmand dashboard tovabbi recept/keszlet/weather elemzese, valamint statisztikai es prediktiv modulok: median, percentilisek, rolling average, anomalia detektalas, regression, Bayes-i frissites, scenario planning es kesobbi ML alapu demand forecasting.
