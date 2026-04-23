# Inventory Direction

Ez a dokumentum az inventory modul UX es domain iranyat tisztazza. A cel az, hogy az inventory resz ne eseti oldalak halmaza legyen, hanem kovetkezetes, bovitheto operativ es controlling felulet.

Kapcsolodo dokumentumok:
- [CURRENT_STATUS.md](C:\BizTracker\docs\CURRENT_STATUS.md)
- [ACCOUNTING_AND_CONTROLLING_MODEL.md](C:\BizTracker\docs\ACCOUNTING_AND_CONTROLLING_MODEL.md)
- [THEORETICAL_STOCK_PREPARATION.md](C:\BizTracker\docs\THEORETICAL_STOCK_PREPARATION.md)

## 1. A jelenlegi helyzet

Jelenleg a frontend inventory reszen kulon menupontok vannak:
- `Inventory Items`
- `Inventory Movements`
- `Stock Levels`

Ez domain szempontbol nem hibas, mert a harom nezet valoban mas szerepet tolt be:
- `Inventory Items` = torzsadat
- `Inventory Movements` = actual operational log
- `Stock Levels` = actual aggregalt keszletszint

Ugyanakkor UX szinten ezek most meg nem alkotnak egyertelmu, vezeto inventory feluletet.

## 2. A celirany

Az inventory modul kesobbi informacioarchitekturaja legyen:

1. `Inventory Overview`
   - inventory landing oldal
   - rovid KPI jellegu attekintes
   - gyors atnavigalas a fo inventory nezetekbe

2. `Inventory Items`
   - torzsadat nezet
   - milyen itemek leteznek
   - item tipusa, aktiv allapota, UOM, stock tracking flag
   - create / edit / archive frontend flow

3. `Inventory Movements`
   - actual operational log
   - mi tortent a keszlettel
   - beszerzes, adjustment, waste, initial_stock
   - kesobbi minimal create frontend flow

4. `Actual Stock Levels`
   - actual movement logbol aggregalt keszlet
   - ez a jelenlegi tenyalapu stock view

5. `Theoretical Stock`
   - kesobbi nezet
   - estimated / modeled stock
   - actualtol kulon kezelve

## 3. Mit mutat az egyes inventory nezet

### Inventory Items
Ez nem keszlet, hanem torzsadat.

Feladata:
- itemek listazasa
- item metaadatok kezelese
- create / edit / archive alap letetele

Nem feladata:
- aktualis keszlet mennyiseg megmutatasa
- stock history megmutatasa

### Inventory Movements
Ez az actual movement log.

Feladata:
- mozgasok listazasa
- audit jellegu visszanezes
- operational nyomkovetes

Nem feladata:
- osszesitett stock level fonezet
- theoretical szamitas

### Stock Levels
Ez az actual stock read modell.

Feladata:
- movement logbol szamolt aktualis mennyiseg
- itemenkenti keszletszint
- utolso mozgas idopontja

Nem feladata:
- inventory item torzsadat szerkesztes
- movement szintu audit reszlet
- estimated consumption

## 4. Miert latszik most reszben ugy, mintha ugyanazt mutatna

Az `Inventory Items` es a `Stock Levels` jelenleg ugyanazokat az itemeket hozzak vissza hasonlo sorstrukturan keresztul. Emiatt a felhasznalonak konnyen tunhet ugy, hogy a ket oldal reszben duplikalja egymast.

A kulonbseg viszont domain szinten lenyeges:
- `Inventory Items` az item letet rogziti
- `Stock Levels` az itemhez tartozo actual quantity-t mutatja

Ezert nem osszevonni kell oket, hanem egyertelmubben kell kommunikani a szerepkoruket.

## 5. Javasolt kovetkezo frontend irany

Rovid tavon a legjobb kovetkezo UI lepes:
- hozzunk letre egy `Inventory Overview` oldalt
- ez legyen az inventory modul landing oldala
- innen lehessen tovabblepni:
  - `Inventory Items`
  - `Inventory Movements`
  - `Actual Stock Levels`

Az overview oldalon kesobb megjelenhet:
- item count
- tracked item count
- stock level row count
- legutobbi movementek
- gyors szuro business unit szerint

Ez dashboard-szeru, de nem valik teljes analytics oldalla.

## 6. Actual vs estimated inventory elv

Az inventory UI-ban kulcsfontossagu, hogy ne keverjuk:
- `actual`
- `estimated`
- `derived`

Ennek megfeleloen:
- `Inventory Movements` = actual
- `Stock Levels` = actual
- kesobbi `Theoretical Stock` = estimated / modeled

Ezt mar most az elnevezesekben es a menustrukturaban is erdemes kovetkezetesen kezelni.

## 7. Route irany a kesobbi egysegesiteshez

A jelenlegi route-ok mukodnek, ezeket most nem kell szetverni. A kesobbi tisztabb celirany viszont ez lehet:

- `/inventory` -> Inventory Overview
- `/inventory/items` -> Inventory Items
- `/inventory/movements` -> Inventory Movements
- `/inventory/stock-levels` -> Actual Stock Levels
- `/inventory/theoretical-stock` -> Theoretical Stock

Ez mar jobban tukrozi az inventory domain belso szerkezetet.

## 8. Implementacios elv

Az inventory modult a kovetkezo sorrendben erdemes boviteni:

1. Inventory Overview oldal
2. Theoretical stock modell dokumentalt elokeszitese
3. Theoretical stock backend read modell
4. Inventory item frontend CRUD alap
5. Inventory movement frontend write alap
6. Kesobbi inventory valuation es FIFO kompatibilis bovites

## 9. Osszefoglalo

Az inventory resz most jo alapokon all, de a kovetkezo fokozatban nem ujabb kulonallo oldalakra, hanem egy tudatos inventory informacioarchitekturara van szukseg.

A helyes irany:
- nem osszemosni az oldalak szerepet
- nem is hagyni oket magyarazat nelkul szetszorva
- hanem egy overview alaprol, egyertelmu actual vs estimated szemlelettel tovabbepiteni oket
