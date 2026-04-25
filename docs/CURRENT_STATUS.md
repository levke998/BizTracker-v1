# BizTracker Current Status

Ez a projekt tenyleges, kodhoz igazított jelenlegi allapotanak igazsagforrasa. Ha gyorsan el kell donteni, mi mukodik mar, mi csak scaffold, mi hianyzik, es mire szabad kovetkezo fejlesztest epiteni, ezt a dokumentumot kell eloszor olvasni.

Fejlesztest vezeto par:
- `CURRENT_STATUS.md` = tenyek es jelenlegi allapot
- `ROADMAP.md` = kovetkezo irany es prioritas

Dokumentacios leltar es elavult/ellentmondasos anyagok:
- [DOCUMENTATION_STATUS.md](DOCUMENTATION_STATUS.md)

Feature kesz definicio:
- egy feature csak akkor kesz, ha van backend endpoint, implementalt use case, ervenyesitett domain szabaly, integration teszt, hasznalt frontend flow, dashboard/UI eleres es frissitett dokumentacio
- mappa, ORM model, route fajl vagy frontend komponens onmagaban nem kesz feature

Kapcsolodo dokumentumok:
- [ROADMAP.md](ROADMAP.md)
- [DATABASE_SYNC_NOTES.md](DATABASE_SYNC_NOTES.md)
- [BUSINESS_DIRECTION.md](BUSINESS_DIRECTION.md)
- [ACCOUNTING_AND_CONTROLLING_MODEL.md](ACCOUNTING_AND_CONTROLLING_MODEL.md)
- [DASHBOARD_DIRECTION.md](DASHBOARD_DIRECTION.md)
- [INVENTORY_DIRECTION.md](INVENTORY_DIRECTION.md)
- [THEORETICAL_STOCK_PREPARATION.md](THEORETICAL_STOCK_PREPARATION.md)
- [POS_INTEGRATION_DIRECTION.md](POS_INTEGRATION_DIRECTION.md)
- [CATALOG_AND_COSTING_DIRECTION.md](CATALOG_AND_COSTING_DIRECTION.md)
- [ARCHITECTURE.md](ARCHITECTURE.md)
- [../PROJECT_DESCRIPTION.md](../PROJECT_DESCRIPTION.md)

## 1. Roviden: hol tartunk most

A projekt mar nem puszta scaffold. Tobb vegponttol frontend oldalig lefuto MVP szelet mukodik:
- master data read
- import upload, CSV parse, import batch detail
- `pos_sales` import profil es finance mapping MVP
- POS ingestion boundary es demo POS tesztkliens
- CSV fallback POS import es API/CSV dedupe vedelem
- finance transaction read
- inventory item CRUD, inventory movement write/read, actual stock level read
- theoretical stock read szerzodes, meg reszben placeholder szamitassal
- estimated consumption audit trail POS fogyas magyarazathoz
- procurement supplier es purchase invoice alap
- purchase invoice posting: finance outflow + inventory purchase movement
- catalog products/ingredients read-write es archive/delete alap
- recipe/BOM adatmodell es seedelt Gourmand receptek
- estimated COGS es margin szamitas receptbol vagy direkt koltsegbol
- Business Dashboard v1 KPI-kkal, trenddel, drill-down endpointokkal es integration tesztekkel
- Identity/auth MVP: login, `/me`, access token, frontend session es route guard

Fo irany:
- a rendszer uzleti elemzo es controlling rendszer, nem CRUD admin
- a frontend vegcel KPI/grafikon/diagram/drill-down alapu
- tablazatok reszletezesre es audit jellegu nezetekre valok
- Clean Architecture + SOLID + modularis monolit marad
- microservice es komplex ML irany nem aktualis, csak kesobbi bovites
- a dashboard profit nem konyvelesi profit
- az estimated stock nem actual stock
- a POS mapping nem stabil SKU mapping
- a theoretical stock endpoint nem kesz theoretical stock engine

## 2. Implementalt es hasznalhato reszek

### Platform / foundation
- FastAPI backend
- PostgreSQL celarchitektura
- Alembic migration pipeline
- env alapu config
- SQLAlchemy 2 stilusu repository wiring
- React + TypeScript + Vite frontend
- TanStack Query alap
- modularis monolit mappaszerkezet

### Identity / auth
- `POST /api/v1/auth/login`
- `GET /api/v1/me`
- login use case email normalizalassal es aktiv user ellenorzessel
- PBKDF2-SHA256 jelszo hash es HMAC-alairt, lejarattal rendelkezo access token
- reusable backend auth dependency/API guard minimum a bearer token ellenorzeshez
- idempotens reference bootstrap seedeli az `admin` es `internal` role-okat, az `app.access` permissiont es az admin usert
- frontend: `/login` oldal, token storage, bearer API header, session read `/me` endpointbol, logout
- protected route: alkalmazasoldalak token nelkul `/login`-ra iranyitanak

### Master data
- `GET /api/v1/master-data/business-units`
- `GET /api/v1/master-data/locations`
- `GET /api/v1/master-data/units-of-measure`
- `GET /api/v1/master-data/categories`
- `GET /api/v1/master-data/products`
- idempotens reference data bootstrap
- Gourmand es Flow demo termekkatalogus seed
- termek ar, sales UOM es opcionális direkt koltseg alap

### Catalog / costing
- `GET /api/v1/catalog/products`
- `POST /api/v1/catalog/products`
- `PATCH /api/v1/catalog/products/{product_id}`
- `DELETE /api/v1/catalog/products/{product_id}` soft archive
- `GET /api/v1/catalog/ingredients`
- `POST /api/v1/catalog/ingredients`
- `PATCH /api/v1/catalog/ingredients/{inventory_item_id}`
- `DELETE /api/v1/catalog/ingredients/{inventory_item_id}` soft archive
- frontend oldalak: `Catalog - Products`, `Catalog - Ingredients`
- termek es alapanyag szerkeszto panelek
- receptes termekeknel aktiv receptverzio, hozam, osszetevok es eloallitasi koltseg
- direkt koltsegu termekeknel `product.default_unit_cost` alapu margin
- alapanyagoknal torzs koltseg, estimated stock es recept-hasznalat darabszam
- g/kg es ml/l atvaltas a receptkoltseg szamitashoz

### Imports / POS ingestion
- `POST /api/v1/imports/files`
- `GET /api/v1/imports/batches`
- `POST /api/v1/imports/batches/{batch_id}/parse`
- `GET /api/v1/imports/batches/{batch_id}/rows`
- `GET /api/v1/imports/batches/{batch_id}/errors`
- `POST /api/v1/imports/batches/{batch_id}/map/financial-transactions`
- `POST /api/v1/pos-ingestion/receipts`
- `pos_sales` profil
- staging sorok, parse hibak, normalized payload
- CSV fallback ugyanabba a dedupe es finance pipeline-ba kerul, mint az API-s ingestion
- dedupe kulcs API es CSV forras kozott

### Finance
- `GET /api/v1/finance/transactions`
- `core.financial_transaction`
- `pos_sales` import -> financial transaction mapping MVP
- `pos_sale` inflow tranzakciok
- `supplier_invoice` outflow tranzakciok procurement postingbol
- source reference es dedupe vedelem
- frontend: `Finance Transactions`

### Demo POS
- `GET /api/v1/demo-pos/catalog`
- `GET /api/v1/demo-pos/receipts`
- `POST /api/v1/demo-pos/receipts`
- frontend: `Demo POS`
- uzletvalasztas, katalogus, kosar, kezi es random nyugta
- demo frontend mar a `pos-ingestion` boundaryt hasznalja nyugtakuldesre
- az utolso nyugtak listaja mar perzisztalt import/finance sorokbol jon, nem csak runtime state
- demo POS szerepe: tesztkliens, nem vegleges kassza

### Inventory
- `GET /api/v1/inventory/items`
- `POST /api/v1/inventory/items`
- `PATCH /api/v1/inventory/items/{item_id}`
- `DELETE /api/v1/inventory/items/{item_id}`
- `GET /api/v1/inventory/movements`
- `POST /api/v1/inventory/movements`
- `GET /api/v1/inventory/stock-levels`
- `GET /api/v1/inventory/theoretical-stock`
- `GET /api/v1/inventory/estimated-consumption`
- inventory item create/edit/archive flow
- inventory movement create flow
- actual stock level aggregacio movement log alapjan
- inventory overview oldal
- POS eladas utani estimated stock csokkenes receptbol vagy direkt trackelt kesztermekbol
- POS eladas utani estimated stock csokkenes audit trail receptes es direkt trackelt fogyasra
- Theoretical Stock frontend oldalrol elerheto estimated consumption audit panel

Fontos hatar:
- `inventory_movement` actual operational log
- `estimated_consumption_audit` estimated fogyasi magyarazat, nem actual keszletmozgas
- `theoretical-stock` endpoint szerzodese letezik, de nem teljes theoretical engine

### Procurement
- `GET /api/v1/procurement/suppliers`
- `POST /api/v1/procurement/suppliers`
- `GET /api/v1/procurement/purchase-invoices`
- `POST /api/v1/procurement/purchase-invoices`
- `POST /api/v1/procurement/purchase-invoices/{purchase_invoice_id}/post`
- supplier list/create backend es frontend
- purchase invoice list/create backend es frontend
- invoice posting status read model
- purchase invoice posting:
  - `supplier_invoice` finance outflow
  - invoice line alapu `purchase` inventory movement
  - source reference az inventory movementen

### Analytics / Dashboard
- `GET /api/v1/analytics/dashboard`
- `GET /api/v1/analytics/dashboard/categories`
- `GET /api/v1/analytics/dashboard/products`
- `GET /api/v1/analytics/dashboard/product-rows`
- `GET /api/v1/analytics/dashboard/expenses`
- `GET /api/v1/analytics/dashboard/expense-source`
- `GET /api/v1/analytics/dashboard/basket-pairs`
- `GET /api/v1/analytics/dashboard/basket-pair-receipts`
- scope-ok: `overall`, `flow`, `gourmand`
- period presetek: `today`, `week`, `month`, `last_30_days`, `year`, `custom`
- KPI-k: revenue, cost, profit, estimated COGS, margin profit HUF, gross margin %, transaction count, average basket value, average basket quantity
- trend chart: valaszthato metrikak
- category -> product drill-down
- product -> source POS rows drill-down
- expense type -> transaction drill-down
- expense transaction -> supplier invoice source drill-down
- frequently bought together / basket-pair read model
- basket-pair -> source receipt detail
- frontend dashboard mar Business Dashboard v1, nem sample oldal

### Tesztelt backend szeletek
Integration tesztek vannak ezekre:
- analytics dashboard
- catalog API
- demo POS API
- finance API
- imports API
- imports finance mapping
- inventory item API
- inventory movements read/write
- inventory stock levels
- inventory theoretical stock
- inventory estimated consumption audit
- procurement supplier API
- procurement purchase invoices
- procurement invoice posting
- identity/auth login es current-user API

A legutobbi dokumentalt teljes integration allapot: `93 passed`.

## 3. Felkesz, reszben kesz vagy placeholder reszek

### Production / recipes
Allapot:
- `core.recipe`, `core.recipe_version`, `core.recipe_ingredient` adatmodell es seedelt BOM van
- catalog oldal mar tud receptes termekhez aktiv receptverziot irni
- production modul router, command/query es frontend production oldalak placeholder jelleguek
- nincs production batch workflow
- nincs batch consumption/output
- nincs waste workflow

Kritikussag:
- Gourmand valodi onkoltseg es theoretical stock oldalhoz kell, de nem kell tul koran tulbonyolitani.

### Flow events
Allapot:
- events modul mappak leteznek
- backend events router placeholder
- frontend events oldalak null komponensek
- nincs event CRUD
- nincs ticket/bar/event cost mapping
- nincs event settlement
- nincs Flow-specifikus dashboard drill-down

Kritikussag:
- Flow elemzesi ertekehez kulcs, de MVP-ben szukitett event management eleg.

### Weather impact analysis
Allapot:
- uzleti es controlling dokumentumokban szerepel
- nincs weather adatmodell/migration
- nincs ingestion
- nincs dashboard vagy korrelacios read model

Kritikussag:
- Gourmand elemzesi szempontbol fontos, de csak stabil sales/product adatok utan erdemes kezdeni.

### FIFO costing / valuation
Allapot:
- beszerzesi invoice line es inventory movement alap elindult
- item default cost es estimated COGS van
- nincs FIFO layer, lot, valuation snapshot vagy consumption costing

Kritikussag:
- fontos controlling irany, de most meg elokeszites kell, nem teljes FIFO engine.

### Frontend UX / dashboard tisztitas
Allapot:
- Dashboard v1 mar valos adatokat hasznal
- sok operational oldal hasznalhato
- events/production oldalak placeholderok
- identity login/session flow mukodik, de UX es permission-kijelzes meg minimalis
- shared loading/error komponensek jelenleg null komponensek
- reszletezo tablazatok hasznosak, de a vegcelhez meg erosebb KPI/chart/drill-down informacioarchitektura kell

Kritikussag:
- az alkalmazas celja miatt a frontend kovetkezo nagy erteke nem ujabb CRUD oldal, hanem elemzesi UX tisztitas.

## 4. Ismert hianyossagok es kockazatok

### Elemzesi kockazatok
- `profit` jelenleg controlling profit: revenue - posted financial outflow.
- `estimated COGS` recept/direkt koltseg alapu becsles, nem FIFO es nem teljes szamviteli COGS.
- `gross margin %` hasznos becsles, de nem vegleges konyvelesi margin.
- product/category bontas import-derived POS sorokbol jon, nem teljesen ugyanaz, mint a finance actual truth.
- basket-pair modell elemzesi read model, nem ajanlorendszer es nem ML.

### Adatminosegi kockazatok
- valodi kasszakod/SKU mapping meg nincs kesz
- CSV export struktura valtozhat
- product_name alapu matching torhet eliras, atnevezes vagy kulso kasszakod hianya miatt
- nincs mapping quarantine a nem illeszkedo POS sorokra
- PDF szamla workflow nincs

### Keszlet es costing kockazatok
- actual es estimated keszlet fogalmat tovabbra is szigoruan kulon kell tartani
- estimated consumption audit letezik, de meg nem teljes theoretical stock engine es nem FIFO valuation
- FIFO nelkul a margin es keszleten allo penz meg becsult
- manual correction history hianyzik

### Biztonsagi / uzemeltetesi kockazatok
- van minimalis auth, de meg nincs finomszemcses route-onkenti role/permission enforcement
- nincs refresh token/session lifecycle
- nincs production-ready audit/security reteg

## 5. Aktualis API felulet

### Health
- `GET /api/v1/health`

### Identity / auth
- `POST /api/v1/auth/login`
- `GET /api/v1/me`

### Master data
- `GET /api/v1/master-data/business-units`
- `GET /api/v1/master-data/locations`
- `GET /api/v1/master-data/units-of-measure`
- `GET /api/v1/master-data/categories`
- `GET /api/v1/master-data/products`

### Catalog
- `GET /api/v1/catalog/products`
- `POST /api/v1/catalog/products`
- `PATCH /api/v1/catalog/products/{product_id}`
- `DELETE /api/v1/catalog/products/{product_id}`
- `GET /api/v1/catalog/ingredients`
- `POST /api/v1/catalog/ingredients`
- `PATCH /api/v1/catalog/ingredients/{inventory_item_id}`
- `DELETE /api/v1/catalog/ingredients/{inventory_item_id}`

### Imports / POS
- `POST /api/v1/imports/files`
- `GET /api/v1/imports/batches`
- `POST /api/v1/imports/batches/{batch_id}/parse`
- `GET /api/v1/imports/batches/{batch_id}/rows`
- `GET /api/v1/imports/batches/{batch_id}/errors`
- `POST /api/v1/imports/batches/{batch_id}/map/financial-transactions`
- `GET /api/v1/demo-pos/catalog`
- `GET /api/v1/demo-pos/receipts`
- `POST /api/v1/demo-pos/receipts`
- `POST /api/v1/pos-ingestion/receipts`

### Finance
- `GET /api/v1/finance/transactions`

### Inventory
- `GET /api/v1/inventory/items`
- `POST /api/v1/inventory/items`
- `PATCH /api/v1/inventory/items/{item_id}`
- `DELETE /api/v1/inventory/items/{item_id}`
- `GET /api/v1/inventory/movements`
- `POST /api/v1/inventory/movements`
- `GET /api/v1/inventory/stock-levels`
- `GET /api/v1/inventory/theoretical-stock`
- `GET /api/v1/inventory/estimated-consumption`

### Procurement
- `GET /api/v1/procurement/suppliers`
- `POST /api/v1/procurement/suppliers`
- `GET /api/v1/procurement/purchase-invoices`
- `POST /api/v1/procurement/purchase-invoices`
- `POST /api/v1/procurement/purchase-invoices/{purchase_invoice_id}/post`

### Analytics
- `GET /api/v1/analytics/dashboard`
- `GET /api/v1/analytics/dashboard/categories`
- `GET /api/v1/analytics/dashboard/products`
- `GET /api/v1/analytics/dashboard/product-rows`
- `GET /api/v1/analytics/dashboard/expenses`
- `GET /api/v1/analytics/dashboard/expense-source`
- `GET /api/v1/analytics/dashboard/basket-pairs`
- `GET /api/v1/analytics/dashboard/basket-pair-receipts`

### Nem aktualisan bekotott placeholder modulok
- production API
- events API

## 6. Jelenlegi adatbazis allapot

Aktualis Alembic head:
- `019_core_estimated_consumption_audit`

Schema-k:
- `auth`
- `core`
- `ingest`
- `analytics`

Fo tablak:
- `auth.user`
- `auth.role`
- `auth.permission`
- `auth.user_role`
- `auth.role_permission`
- `core.business_unit`
- `core.location`
- `core.unit_of_measure`
- `core.category`
- `core.product`
- `core.financial_transaction`
- `core.inventory_item`
- `core.inventory_movement`
- `core.estimated_consumption_audit`
- `core.supplier`
- `core.supplier_invoice`
- `core.supplier_invoice_line`
- `core.recipe`
- `core.recipe_version`
- `core.recipe_ingredient`
- `ingest.import_batch`
- `ingest.import_file`
- `ingest.import_row`
- `ingest.import_row_error`

DB-validacio es migracios reszletek: [DATABASE_SYNC_NOTES.md](DATABASE_SYNC_NOTES.md).

## 7. Kovetkezo fejlesztesi fokuszok

A kovetkezo fejleszteseket ne izolalt CRUD feature-kent kezeljuk, hanem az uzleti elemzesi vegcel fele vezeto szeletekkent:

1. Frontend UX / dashboard tisztitas
   - Dashboard v1 informacioarchitektura finomitasa
   - KPI, chart, drill-down es reszletezo panelek tisztabb hierarchiaja
   - operational tablazatok szerepenek pontosabb elkulonitese

2. POS/SKU mapping es source-data workflow
   - kulso kasszakod -> BizTracker product mapping
   - missing mapping quarantine
   - CSV fallback tovabbi validacio

3. FIFO costing elokeszites
   - invoice line / purchase movement / cost source osszekotese
   - valuation-ready adatmodell
   - teljes FIFO engine nelkul

4. Flow event management MVP
   - event CRUD minimum
   - ticket/bar revenue hozzarendeles elokeszitese
   - event cost es settlement lite

5. Weather impact analysis elokeszites
   - Szolnok weather observation adatmodell
   - sales/weather idosav osszekotes
   - elso korrelacios dashboard slice

6. Kesobbi ML modellek
   - csak tiszta lineage es stabil historical data utan
   - eloszor forecast/ajanlas kutatasi irany, nem core mukodes

Reszletes prioritas: [ROADMAP.md](ROADMAP.md).

## 8. Gyors lokal futtatas

Seedelt user: admin@biztracker.local
Seedelt jelszó: ChangeMe123!

Backend:

```powershell
cd C:\BizTracker\backend
python -m uvicorn app.main:app --reload
```

Frontend:

```powershell
cd C:\BizTracker\frontend
npm.cmd run dev
```
