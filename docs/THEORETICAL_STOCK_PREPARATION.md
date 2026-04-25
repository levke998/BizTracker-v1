# Theoretical Stock Preparation

Ez a dokumentum a theoretical / estimated stock modell elso dokumentalt elokeszitese. A cel most nem implementacio, hanem tiszta domain hatar kijelolese, hogy a kesobbi fejlesztes ne keverje ossze az actual es estimated inventory retegeket.

Kapcsolodo dokumentumok:
- [DOCUMENTATION_STATUS.md](C:\BizTracker\docs\DOCUMENTATION_STATUS.md)
- [ACCOUNTING_AND_CONTROLLING_MODEL.md](C:\BizTracker\docs\ACCOUNTING_AND_CONTROLLING_MODEL.md)
- [CURRENT_STATUS.md](C:\BizTracker\docs\CURRENT_STATUS.md)
- [INVENTORY_DIRECTION.md](C:\BizTracker\docs\INVENTORY_DIRECTION.md)

## 1. Mi a theoretical stock

Az `actual stock` azt mutatja, amit a tenyleges movement log alapjan tudunk.

Az `theoretical stock` azt mutatja, amit a modell szerint keszleten kellene latnunk.

Ez nem ugyanaz.

Egyszeru szemlelet:

`theoretical stock = actual incoming actuals - estimated consumption + actual corrections`

MVP szinten a teljes theoretical engine meg nincs kesz. Van viszont kulon read szerzodes es van egy egyszerusitett `estimated_stock_quantity` mezore epulo becsult keszletcsokkentes POS eladas utan. Ezt a ket dolgot nem szabad osszemosni.

## 2. Mi mar van meg hozza

Mar letezik:
- `inventory_item`
- `inventory_movement`
- `inventory_item.estimated_stock_quantity`
- actual movement tipusok:
  - `purchase`
  - `adjustment`
  - `waste`
  - `initial_stock`
- actual stock level read modell
- `recipe`
- `recipe_version`
- `recipe_ingredient`
- POS ingestion utani estimated stock csokkenes recept vagy direkt trackelt kesztermek alapjan

Ez jo alapot ad a theoretical stock kesobbi bevezetesehez.

## 3. Mi nincs meg hozza meg

A theoretical stockhoz meg hianyzik:
- kulon estimated consumption audit tabla
- source receipt / import row szintu traceability
- production / batch logika
- inventory valuation logika
- actual vs theoretical variance read modell
- theoretical quantity valodi bekotese a read endpointba

## 4. Actual vs theoretical elv

Kulcselv:
- `actual stock` = tenyleges operational truth
- `theoretical stock` = modeled / estimated truth

Ezert a ketto ne ugyanabban a mezoben, ne ugyanabban a tablaban, es ne ugyanabban a fogalomban eljen.

Kesobb a rendszernek ki kell tudnia mutatni:
- actual quantity
- theoretical quantity
- variance quantity

## 5. Gourmand oldali theoretical stock alap

A Gourmand eseteben a theoretical stock alapjanak fo bemenetei:
- sales actuals
- product -> recipe kapcsolat
- recipe version
- yield
- ingredient consumption rules

Egyszeru jovo beli logika:

`sales -> sold product qty -> recipe version -> estimated ingredient consumption`

Ebbol kepzodik:
- estimated ingredient outflow
- theoretical stock

## 6. Flow oldali theoretical stock alap

A Flow eseteben a bar oldali theoretical stock kesobbi alapjai:
- bar sales actuals
- product to inventory mapping
- ital / adagolas szabalyok
- event context opcionalisan

Itt nincs feltetlen teljes recept modell, de lesznek consumption szabalyok.

## 7. Amit nem szabad elrontani

Most sem es kesobb sem szabad:
- az estimated fogyast actual movementkent tarolni
- a theoretical stockot actual stocknak nevezni
- egyetlen stock mezobe osszeonteni a ket reteg adatait

Az alapelv:
- actual maradjon actual
- estimated maradjon estimated
- a kulonbseg kulon szamolhato variance legyen

## 8. Elso read modell allapot

Az elso theoretical stock backend read modell mar letezik. A jelenlegi szerzodes:
- `inventory_item_id`
- `business_unit_id`
- `actual_quantity`
- `theoretical_quantity`
- `variance_quantity`
- `last_actual_movement_at`
- `last_estimated_event_at`
- `estimation_basis`

Jelenlegi MVP jelentese:
- `actual_quantity` az actual stock level read modellbol jon
- `theoretical_quantity` jelenleg `null`
- `variance_quantity` jelenleg `null`
- `estimation_basis` jelenleg `not_configured`

Ez tudatos atmeneti allapot:
- mar van kulon szerzodes az estimated reteghez
- de meg nincs bekotve audit trail alapu recipe vagy sales alapu theoretical szamitas
- igy nem keverjuk ossze a valos es a modellalt mennyiseget

Fontos pontositas:
- a POS ingestion mar csokkentheti az `inventory_item.estimated_stock_quantity` mezot
- ez hasznos MVP-s becsult keszletjelzes
- de ez meg nem teljes theoretical stock engine
- kovetkezo kritikus lepes a kulon audit trail, hogy minden becsult fogyas forrasig visszakeresheto legyen

## 9. Elso implementacios sorrend

Javasolt sorrend:

1. estimated consumption audit trail
2. source receipt/import row -> product -> recipe/direct inventory item traceability
3. actual vs theoretical frontend osszehasonlito nezet tisztitasa
4. theoretical quantity es variance elso valodi szamitasa
5. manual correction history

## 10. Osszefoglalo

A theoretical stock a kovetkezo nagy inventory reteget jelenti, de csak ugy lesz ertelmes, ha:
- kulon marad az actual movement logtol
- kulon marad az actual stock leveltol
- vilagosan labeled, magyarazhato modellkent jelenik meg

Ez a dokumentum ezt az iranyt rogziti, hogy a kovetkezo implementacios kor mar stabil domain alapra epuljon.
