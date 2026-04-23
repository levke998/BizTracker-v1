# BizTracker MVP Implementation Plan

Ez a dokumentum a BizTracker MVP fejlesztési sorrendjét rögzíti. A cél egy reális, fokozatos implementációs terv, amely clean architecture és SOLID elvek mentén halad, de nem próbál meg túl sokat lefedni az első verzióban.

Kapcsolódó dokumentumok:
- [PROJECT_DESCRIPTION.md](C:\BizTracker\PROJECT_DESCRIPTION.md)
- [ARCHITECTURE.md](C:\BizTracker\docs\ARCHITECTURE.md)
- [MIGRATION_PLAN.md](C:\BizTracker\docs\MIGRATION_PLAN.md)

## 1. Tervezési alapelvek

Az MVP célja nem egy teljes ERP, hanem egy működő belső üzleti rendszer első verziója, amely:
- belső felhasználókkal használható
- képes adatot importálni a jelenlegi forrásrendszerekből
- kezeli a legfontosabb operatív törzsadatokat
- ad alap pénzügyi és készlet láthatóságot
- támogatja a két üzlet összehasonlítását
- előkészíti a későbbi production és events specifikus bővítést

Explicit feltételezések:
- az MVP elsődleges adatforrása CSV/Excel import
- a kassza- és külső API integrációk később is kiválthatók maradnak
- az analitika első körben read model és aggregált lekérdezések szintjén marad
- a production és events modul MVP-ben szűkített funkciókört kap

## 2. Javasolt implementációs sorrend modulonként

Az ajánlott sorrend:
1. platform foundation
2. identity
3. core master data
4. imports
5. finance
6. inventory
7. procurement
8. analytics
9. production
10. events

Megjegyzés: a `platform foundation` nem önálló üzleti modul, hanem a futtatható backend/frontend alap és a közös technikai keret.

## 3. Modulonkénti részletes sorrend

### 3.1. Platform foundation

**Cél**
- futtatható backend és frontend alap létrehozása
- config, db session, auth wiring, root routing, query client, route shell kialakítása
- fejlesztői alapok: migration, logging, env, testing skeleton

**Függőségek**
- nincs üzleti modul függőség

**Miért ez jön először**
- minden további modul erre épít
- nélküle a use case-ek és migrationök párhuzamosan sem fejleszthetők stabilan

**MVP deliverable**
- indítható FastAPI app
- indítható frontend app
- működő DB connection alap
- Alembic inicializáció

### 3.2. Identity

**Cél**
- belső felhasználók hitelesítése
- szerepkörök és alapszintű jogosultságkezelés
- védett route-ok és backend endpointok

**Függőségek**
- platform foundation

**Miért itt jön**
- mivel belső rendszer készül, a többi modulhoz szükséges a bejelentkezés és access control
- backend és frontend fejlődése is ezzel lesz biztonságosan tesztelhető

**MVP fókusz**
- login
- current user lekérdezés
- role-alapú minimum jogosultság

### 3.3. Core master data

**Cél**
- közös törzsadatok kezelése
- business unit, location, category, unit of measure, product alapok

**Függőségek**
- platform foundation
- identity

**Miért itt jön**
- a finance, inventory, procurement, production és events is törzsadatokra épít
- a helyes domain-határokat itt kell először lefektetni

**MVP fókusz**
- business unit kiválasztás
- alap kategóriák és termékek
- telephelyek

### 3.4. Imports

**Cél**
- CSV/Excel import pipeline alap kialakítása
- import batch, státusz, hibanaplózás, staging

**Függőségek**
- platform foundation
- identity
- core master data

**Miért itt jön**
- az MVP fő adatbetöltési módja várhatóan import lesz
- a finance, inventory és később analytics modul haszna ettől függ

**MVP fókusz**
- fájlfeltöltés
- import batch nyilvántartás
- sorhiba és feldolgozási státusz

### 3.5. Finance

**Cél**
- bevétel és kiadás nyilvántartás
- alap pénzügyi tranzakciók és listázások

**Függőségek**
- identity
- core master data
- imports

**Miért itt jön**
- üzleti értéket nagyon gyorsan ad
- dashboard és összehasonlítás első verziója már erre építhető
- sok importált adat először pénzügyi oldalról lesz hasznos

**MVP fókusz**
- revenue/expense tranzakciók
- időszaki listázás
- business unit szerinti szűrés

### 3.6. Inventory

**Cél**
- készletelemek, raktárak, készletmozgások kezelése
- minimum készletszint láthatóság

**Függőségek**
- identity
- core master data
- imports
- részben finance

**Miért itt jön**
- a cukrászda működéséhez ez kritikus
- de a helyes inventory modellezéshez előbb kell törzsadat és import alap
- túl korán elkezdve könnyen hibás domain döntéseket hozunk

**MVP fókusz**
- inventory item
- warehouse
- stock movement
- stock level lekérdezés

### 3.7. Procurement

**Cél**
- beszállítók, beszerzések, bejövő számlák kezelése

**Függőségek**
- identity
- core master data
- finance
- inventory

**Miért itt jön**
- procurement szorosan kapcsolódik a készlethez és a pénzügyhöz
- érdemes csak akkor bevezetni, amikor a kapcsolódó alapok már stabilak

**MVP fókusz**
- supplier
- supplier invoice
- purchase order light

### 3.8. Analytics

**Cél**
- közös dashboardok
- KPI-k
- üzlet-összehasonlítás
- historikus riport alap

**Függőségek**
- identity
- finance
- inventory
- imports
- opcionálisan procurement

**Miért itt jön**
- analitika csak akkor értékes, ha már van megbízható operatív adat
- az MVP-ben ez ne előzze meg az adatforrások stabilizálását

**MVP fókusz**
- dashboard
- időszaki trendek
- business unit comparison

### 3.9. Production

**Cél**
- Gourmand gyártási logika első verziója
- receptek és batch-ek minimum kezelése

**Függőségek**
- identity
- core master data
- inventory
- procurement

**Miért itt jön**
- ez üzletileg fontos, de domain szempontból érzékeny
- csak stabil inventory modell után érdemes bevezetni
- különben könnyen át kellene írni a készletlogikát

**MVP fókusz**
- recipe
- recipe version
- production batch
- alapanyag fogyás lekövetésének minimum alapja

### 3.10. Events

**Cél**
- Flow eseménykezelés és eseményalapú bevétel-elemzés első verziója

**Függőségek**
- identity
- core master data
- finance
- imports
- analytics részben

**Miért itt jön**
- az esemény-specifikus logika viszonylag jól leválasztható
- a pénzügyi és import alapok megléte után már gyorsabban felépíthető
- a MVP-ben szűkítve érdemes bevezetni

**MVP fókusz**
- event
- ticket/bar revenue summary
- event expense
- event profitability lite

## 4. MVP-hez ajánlott implementációs fázisok

### Fázis 1
- platform foundation
- identity
- core master data

### Fázis 2
- imports
- finance
- inventory

### Fázis 3
- procurement
- analytics

### Fázis 4
- production
- events

Ez a bontás azért jó, mert minden fázis végén már demonstrálható üzleti érték keletkezik.

## 5. Az első 10 backend use case

Az első implementálandó use case-ek ajánlott sorrendben:

1. `identity.login`
   - felhasználó bejelentkezés access tokennel
2. `identity.get_current_user`
   - aktuális felhasználó és szerepkör lekérdezése
3. `master_data.list_business_units`
   - elérhető üzleti egységek listázása
4. `master_data.list_locations`
   - telephelyek listázása business unit szerint
5. `imports.upload_import_file`
   - import fájl feltöltése és batch létrehozása
6. `imports.list_import_batches`
   - import előzmények és státuszok lekérdezése
7. `finance.create_transaction`
   - bevétel vagy kiadás rögzítése
8. `finance.list_transactions`
   - pénzügyi tranzakciók listázása szűrőkkel
9. `inventory.create_inventory_item`
   - készletelem létrehozása
10. `inventory.register_stock_movement`
   - készletmozgás rögzítése

Közvetlenül ezután ajánlott további use case-ek:
- `inventory.get_stock_levels`
- `procurement.create_supplier`
- `procurement.create_supplier_invoice`
- `analytics.get_dashboard_data`
- `analytics.get_business_comparison`

## 6. Az első 10 frontend képernyő vagy flow

Ajánlott sorrend:

1. `LoginPage`
   - bejelentkezési flow
2. `App shell + protected routing`
   - layout, sidebar, topbar, route guard
3. `Business unit switcher`
   - aktív üzlet kiválasztása
4. `DashboardPage`
   - első alap KPI nézet placeholder és később valós adatok
5. `ImportCenterPage`
   - fájlfeltöltés és batch státuszok
6. `TransactionsPage`
   - pénzügyi tranzakció lista és alap szűrés
7. `InventoryListPage`
   - készletelemek listája
8. `StockLevelsPage`
   - készletszintek nézet
9. `SuppliersPage`
   - beszállítók listája
10. `BusinessComparisonPage`
   - két üzlet összehasonlító analitika

Közvetlenül ezután ajánlott képernyők:
- `InvoicesPage`
- `RecipesPage`
- `ProductionBatchesPage`
- `EventsPage`
- `EventDetailPage`

## 7. Mi maradjon stub az MVP-ben

Érdemes stubként hagyni:
- automatikus POS API integráció
- időjárás automatikus adatlekérés
- összetett receptköltség és hozamszámítás
- selejt és veszteség finom részletezése
- teljes purchase order workflow
- komplex event settlement logika
- predikciók és ajánlások
- anomália detekció
- advanced analytics aggregációk
- granular permission matrix

Miért jó stubként hagyni:
- ezek üzletileg fontosak, de nagy domain-kockázatot hordoznak
- az MVP fő célja a stabil adatáramlás és operatív alapok megteremtése

## 8. Kockázatok az MVP implementációs sorrendben

### Import adatminőség
- a CSV/Excel források struktúrája változó lehet
- emiatt az import modulnál korai normalizációs döntések kockázatosak

### Inventory domain komplexitás
- a készlet, termék, alapanyag és gyártás kapcsolata könnyen túlbonyolódik
- ezért production csak inventory után javasolt

### Analytics túl korai bevezetése
- ha még nincs stabil adatmodell, az analitikai nézetek félrevezetők lehetnek
- ezért analytics az operatív modulok után jön

### Túl nagy MVP veszélye
- ha egyszerre akarjuk a teljes Gourmand és Flow specifikus logikát, szétcsúszik a scope
- ezért a specifikus modulok csak szűkített változatban kerüljenek be

## 9. Ajánlott MVP scope határ

Reális MVP:
- auth
- business unit és location törzsadat
- import batch és fájlfeltöltés
- pénzügyi tranzakció alap
- inventory alap
- procurement minimum
- dashboard és comparison minimum
- production minimum
- events minimum

Nem reális MVP első körre:
- teljes recept és gyártásoptimalizáció
- mély költségallokáció
- teljes eseményelszámolási motor
- automatizált külső integrációs ökoszisztéma

## 10. Ajánlott következő tervezési lépések

A jelen dokumentum után érdemes elkészíteni:
- a `master data` pontos domain modelljét
- az első Alembic migration backlogot konkrét táblalistával
- az első sprint use case bontását
- az első API contract vázat

