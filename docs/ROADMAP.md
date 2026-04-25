# BizTracker Roadmap

Ez a dokumentum a fejlesztest vezeto roadmap. A `CURRENT_STATUS.md` tenyszeru allapotara epul, es azt mondja meg, merre kell tovabblepni ugy, hogy a projekt ne essen szet CRUD oldalakra.

Igazsagforras-par:
- [CURRENT_STATUS.md](CURRENT_STATUS.md) - mi van kesz, mi felkesz, mi hianyzik
- [ROADMAP.md](ROADMAP.md) - mit fejlesztunk kovetkezonek es miert

Dokumentacios allapot:
- [DOCUMENTATION_STATUS.md](DOCUMENTATION_STATUS.md)
- [UX_REDESIGN_ROADMAP.md](UX_REDESIGN_ROADMAP.md)

## 1. Strategiai cel

A BizTracker celja uzleti elemzo es controlling rendszer:
- KPI-k
- diagramok
- trendek
- drill-down
- adatforrasig kovetheto elemzes

Nem cel:
- egyszeru CRUD adminna valni
- tul koran microservice iranyba menni
- bizonytalan adatminosegre komplex ML-t epiteni
- actual es estimated retegeket osszekeverni

Architektura:
- Clean Architecture
- SOLID
- modularis monolit
- PostgreSQL + analytics/read-model reteg ugyanabban a rendszerben

## 2. Ami mar kesz vagy hasznalhato

### Foundation
- FastAPI backend
- React + TypeScript + Vite frontend
- Alembic migration pipeline
- modularis monolit mappaszerkezet
- integration test alap
- Identity/auth MVP: login, `/me`, access token, frontend session es route guard

### Imports / POS / finance
- import upload, parse, rows/errors
- `pos_sales` profil
- finance mapping MVP
- POS ingestion boundary
- demo POS tesztkliens
- CSV fallback
- API/CSV dedupe key
- finance transaction read API es frontend

### Inventory / procurement / catalog
- inventory item CRUD
- inventory movement write/read
- actual stock levels
- theoretical stock read contract
- procurement supplier es purchase invoice alap
- purchase invoice posting finance es inventory actual iranyba
- catalog product/ingredient read-write alap
- recept/BOM adatmodell
- estimated COGS es margin szamitas

### Analytics / dashboard
- Business Dashboard v1
- `overall`, `flow`, `gourmand` scope
- period presetek
- KPI-k es trend chart
- category/product/expense drill-down
- product -> source POS rows
- expense transaction -> supplier invoice source
- basket-pair / frequently bought together read model
- basket-pair -> source receipt detail
- dashboard integration tests

## 3. Aktiv fejlesztesi irany

Most nem uj nagy modult kell vakon kezdeni, hanem a mar mukodo adatfolyamokat kell magyarazhatova, biztonsagosabba es elemzeskozpontuabba tenni.

Aktiv irany:
- frontend UX/dashboard takaritas
- POS/SKU mapping es source-data workflow
- FIFO costing elokeszites
- Flow event management MVP elokeszitese
- weather impact analysis elokeszitese

## 4. Kovetkezo 7 fejlesztesi fokusz

### 1. Frontend UX / dashboard takaritas

Cel:
- a frontend egyre inkabb uzleti elemzo rendszernek hasson
- a dashboard legyen a dontesi kozpont
- tablazatok csak drill-down, audit es reszletezes szerepben legyenek
- a felulet magyar nyelvu, ekezetes, user friendly business alkalmazas legyen, ne admin panel

Konkreten:
- magyar UI-szovegek es technikai label mapping
- sidebar/header egyszerusites, Activity ikon + BizTracker logo irany
- Catalog lenyilo menu es Inventory menuk logikus beolvasztasa
- Dashboard v1 KPI/chart/detail panelek vizualis es UX tisztitasa
- `overall`, `flow`, `gourmand` scope valtas erositese
- category/product/expense/basket drill-down panelek egységesitese
- inventory/procurement/finance oldalak szerepenek egyertelmu elkulonitese
- placeholder oldalak eltuntetese vagy tudatos elrejtese a navigaciobol

Reszletes UX redesign terv:
- [UX_REDESIGN_ROADMAP.md](UX_REDESIGN_ROADMAP.md)

Miert most:
- a business-analysis cel ettol lesz lathato a felhasznalonak
- az alkalmazas ne tunjon sima admin feluletnek

### 2. Identity/auth MVP

Allapot:
- end-to-end MVP kesz
- `POST /api/v1/auth/login`
- `GET /api/v1/me`
- access token flow
- frontend token storage es session state
- route guard
- API dependency guard minimum
- seedelt admin/internal role es admin user bootstrap

Nem most:
- bonyolult SSO
- finom szemcses permission matrix minden route-ra
- audit/compliance full scope

### 3. Estimated stock audit trail

Allapot:
- end-to-end MVP kesz
- `core.estimated_consumption_audit` modell es migration
- `GET /api/v1/inventory/estimated-consumption`
- receipt/import row -> product -> recipe/direct item -> consumed inventory item kapcsolat
- mennyiseg, UOM, estimation basis, timestamp, before/after quantity
- dedupe kompatibilis mukodes
- Theoretical Stock frontend oldalrol elerheto audit detail panel

Kovetkezo bovites kesobb:
- theoretical stock variance motorba bekotes
- POS/SKU mapping utan stabilabb product resolution
- kesobbi theoretical stock, variance es ML alapja lesz

### 4. POS/SKU mapping es source-data workflow

Cel:
- a valodi kasszaprogramhoz valo csatlakozas ne product_name matchingen muljon

Konkreten:
- kulso kasszakod / SKU / barcode alias modell
- mapping felulet
- missing mapping quarantine
- CSV fallback validacios riport
- product rename kompatibilitas

Miert fontos:
- a dashboard es estimated stock csak akkor megbizhato, ha a POS sorok stabilan termekhez kothetok

### 5. FIFO costing elokeszites

Cel:
- a mostani cost/margin reteg ne zarja ki a kesobbi FIFO-t

Konkreten:
- purchase invoice line, inventory movement es cost source kapcsolat tisztitasa
- valuation-ready metadata
- latest/default cost es estimated COGS elkulonitese
- actual cost vs estimated cost fogalmak pontos dokumentalasa

Nem most:
- teljes FIFO engine
- bonyolult lot management
- teljes konyvelesi keszletertekeles

### 6. Flow event management MVP

Cel:
- a Flow oldal ne csak altalanos sales dashboard legyen, hanem event profitability iranyba induljon

Konkreten:
- event CRUD minimum
- event date, title, status, business unit/location
- ticket revenue es bar revenue hozzarendeles elokeszitese
- event cost alap
- settlement lite: revenue - event cost
- dashboard drill-down event scope iranyba

Nem most:
- komplex performer payout engine
- teljes event settlement szabalyhalmaz
- kulso jegyrendszer integracio

### 7. Weather impact analysis elokeszites

Cel:
- Gourmand oldalon az idojaras-hatas kesobb merheto legyen

Konkreten:
- weather observation adatmodell Szolnok fokuszra
- 3 oras vagy napi elemzesi ablak dontese
- sales aggregation idosavhoz kotese
- fagylalt/sutemeny kategoriakra elso korrelacios read model

Nem most:
- ML prediction
- automatikus donteshozatal
- tul reszletes meteorologiai modell

## 5. Kesobbi ML modellek

ML csak kesobb jo irany, amikor mar van:
- stabil POS/source lineage
- eleg historikus adat
- audit trail estimated consumptionre
- tiszta product/category mapping
- weather/event context

Lehetseges kesobbi modellek:
- napi forgalom forecast
- termekkategoria demand forecast
- weather-sensitive demand analysis
- basket recommendation
- keszletbeszerzesi ajanlas
- anomalia detekcio

Fontos:
- ML ne legyen core mukodesi dependency
- eloszor magyarazhato statisztikai/read-model elemzes kell
- ajanlas mindig legyen visszavezetheto adatra

## 6. Prioritasi javaslat

Ha egy kovetkezo kodolas-orientalt sprintet kell valasztani:

1. Dashboard UX es drill-down tisztitas
2. POS/SKU mapping
3. FIFO costing elokeszites
4. Flow event MVP
5. Weather impact MVP
6. Finomszemcses authorization es session lifecycle kesobb, ha a termekhasznalat indokolja

Indok:
- a dashboard UX a business-analysis cel lathatosagat emeli
- a POS/SKU mapping a business-analysis adatok megbizhatosagat teszi rendbe, mert az audit trail mar lathatova tette a product matching fontossagat
- a FIFO elokeszites megorzi a kesobbi controlling iranyt
- a Flow es weather irany uzletspecifikus elemzesi erteket ad
- az identity/auth MVP es az estimated stock audit trail mar kesz

## 6/A. Konkret kovetkezo lepes

A kovetkezo konkret fejlesztesi lepes:

`POS/SKU mapping es source-data workflow`

Miert ez:
- az identity/auth MVP es az estimated stock audit trail kesz
- az audit trail most mar megmutatja, ha product_name alapu matching miatt rossz vagy hianyzo fogyasi magyarazat keletkezne
- a kovetkezo adatbizalmi lepes a kulso kasszakod/SKU/barcode alias es missing mapping workflow
- ez kozvetlenul erositi a dashboard, estimated stock es kesobbi FIFO/theoretical stock megbizhatosagat

## 7. Dontesi elvek

Minden kovetkezo fejlesztesnel:
- domain jelentese legyen tiszta
- backend read/write szelet legyen stabil
- frontend az elemzesi UX-et tamogassa
- actual es estimated retegek ne keveredjenek
- tabla csak akkor legyen fonezet, ha audit/reszletezes a cel
- ne kezdjunk microservice bontast
- ML csak historical data es lineage utan jojjon

## 8. Kozep tavu moduliranyok

### Gourmand
- recipe UX erositese
- estimated consumption audit
- theoretical stock variance
- product/category profitability
- weather impact

### Flow
- event model MVP
- ticket/bar revenue bontas
- event cost
- event profitability lite
- kesobb performer settlement

### Finance / procurement
- finance write workflow
- koltseg oldali strukturalt mapping
- PDF/manual invoice workflow
- source-to-dashboard traceability

### Inventory / costing
- estimated stock audit
- actual vs estimated variance
- valuation-ready model
- FIFO compatible preparation

### Dashboard / analytics
- business owner first dashboard
- scope-specific dashboards
- KPI -> chart -> drill-down -> source record
- eventual recommendations, not early black-box ML
