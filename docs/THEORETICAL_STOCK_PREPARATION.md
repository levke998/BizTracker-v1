# Theoretical Stock Preparation

Ez a dokumentum a theoretical / estimated stock modell elso dokumentalt elokeszitese. A cel most nem implementacio, hanem tiszta domain hatar kijelolese, hogy a kesobbi fejlesztes ne keverje ossze az actual es estimated inventory retegeket.

Kapcsolodo dokumentumok:
- [ACCOUNTING_AND_CONTROLLING_MODEL.md](C:\BizTracker\docs\ACCOUNTING_AND_CONTROLLING_MODEL.md)
- [CURRENT_STATUS.md](C:\BizTracker\docs\CURRENT_STATUS.md)
- [INVENTORY_DIRECTION.md](C:\BizTracker\docs\INVENTORY_DIRECTION.md)

## 1. Mi a theoretical stock

Az `actual stock` azt mutatja, amit a tenyleges movement log alapjan tudunk.

Az `theoretical stock` azt mutatja, amit a modell szerint keszleten kellene latnunk.

Ez nem ugyanaz.

Egyszeru szemlelet:

`theoretical stock = actual incoming actuals - estimated consumption + actual corrections`

MVP szinten ezt meg nem implementaljuk, csak az alapelveit rogzitjuk.

## 2. Mi mar van meg hozza

Mar letezik:
- `inventory_item`
- `inventory_movement`
- actual movement tipusok:
  - `purchase`
  - `adjustment`
  - `waste`
  - `initial_stock`
- actual stock level read modell

Ez jo alapot ad a theoretical stock kesobbi bevezetesehez.

## 3. Mi nincs meg hozza meg

A theoretical stockhoz meg hianyzik:
- recipe / BOM kezeles
- recipe version fogalma
- sales to consumption mapping
- production / batch logika
- inventory valuation logika
- actual vs theoretical variance read modell

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
- de meg nincs bekotve recipe vagy sales alapu becsles
- igy nem keverjuk ossze a valos es a modellalt mennyiseget

## 9. Elso implementacios sorrend

Javasolt sorrend:

1. recipe / consumption szabalyok minimal domain elokeszitese
2. sales -> estimated consumption alapelvek rogzitese
3. actual vs theoretical frontend osszehasonlito nezet
4. theoretical quantity es variance elso valodi szamitasa

## 10. Osszefoglalo

A theoretical stock a kovetkezo nagy inventory reteget jelenti, de csak ugy lesz ertelmes, ha:
- kulon marad az actual movement logtol
- kulon marad az actual stock leveltol
- vilagosan labeled, magyarazhato modellkent jelenik meg

Ez a dokumentum ezt az iranyt rogziti, hogy a kovetkezo implementacios kor mar stabil domain alapra epuljon.
