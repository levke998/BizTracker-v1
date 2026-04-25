# BizTracker Documentation Status

Ez a dokumentum a dokumentacios allapot leltara. A cel, hogy egyertelmu legyen:
- melyik dokumentum az igazsagforras
- melyik dokumentum csak hatter vagy torteneti terv
- mi elavult
- mi van mar implementalva
- mi hianyzik
- hol vannak ellentmondasok

## 1. Kinevezett igazsagforras

### Tenyleges allapot

Igazsagforras:
- [CURRENT_STATUS.md](CURRENT_STATUS.md)

Szerepe:
- implementalt endpointok
- mukodo frontend oldalak
- felkesz/placeholder modulok
- hianyossagok es kockazatok
- aktualis Alembic head osszefoglalo

### Fejlesztest vezeto roadmap

Igazsagforras:
- [ROADMAP.md](ROADMAP.md)

Szerepe:
- aktiv fejlesztesi fokusz
- kovetkezo prioritasok
- kozep tavu irany
- mit ne kezdjunk tul koran

### DB es teszt validacio

Igazsagforras:
- [DATABASE_SYNC_NOTES.md](DATABASE_SYNC_NOTES.md)

Szerepe:
- Alembic head
- migracios valtozasok
- fo gepes DB-validacio
- futtatott tesztek es eredmenyek

### Eredeti termekvizió

Forras:
- [../PROJECT_DESCRIPTION.md](../PROJECT_DESCRIPTION.md)

Szerepe:
- hosszabb tavu termek- es domain-vizio
- nem napi implementacios statusz
- nem endpoint igazsagforras

## 2. Dokumentumok szerepkore

| Dokumentum | Aktualis szerep | Allapot |
|---|---|---|
| `CURRENT_STATUS.md` | tenyleges projektallapot | igazsagforras |
| `ROADMAP.md` | fejlesztest vezeto roadmap | igazsagforras |
| `DOCUMENTATION_STATUS.md` | dokumentacios leltar es ellentmondaslista | igazsagforras a doksik rendjere |
| `DATABASE_SYNC_NOTES.md` | DB/migration/teszt sync | igazsagforras DB-re |
| `BUSINESS_DIRECTION.md` | uzleti cel es elemzesi filozofia | aktualis hatter |
| `ACCOUNTING_AND_CONTROLLING_MODEL.md` | actual vs estimated, controlling modell | aktualis hatter |
| `DASHBOARD_DIRECTION.md` | dashboard contract es drill-down irany | aktualis |
| `UX_REDESIGN_ROADMAP.md` | magyar business UX, dashboard es navigacio redesign roadmap | aktualis |
| `INVENTORY_DIRECTION.md` | inventory UX/domain irany | aktualis |
| `THEORETICAL_STOCK_PREPARATION.md` | theoretical/estimated stock domain hatar | aktualis, audit trail MVP utan variance engine elott |
| `POS_INTEGRATION_DIRECTION.md` | demo POS vs valodi POS boundary | aktualis |
| `CATALOG_AND_COSTING_DIRECTION.md` | catalog, recipe cost, margin | aktualis |
| `ARCHITECTURE.md` | Clean Architecture es modularis monolit | aktualis hatter |
| `MVP_IMPLEMENTATION_PLAN.md` | eredeti MVP sorrend | reszben torteneti |
| `MIGRATION_PLAN.md` | eredeti migration terv | reszben torteneti |
| `IDENTITY_CORE_MODEL_PLAN.md` | identity/core kezdeti modellezes es auth MVP statusz | reszben torteneti, auth MVP resze frissitve |
| `INITIAL_STRUCTURE.md` | kezdeti mappaszerkezet | torteneti |
| `IMPORT_PROFILES.md` | import profil szabalyok | aktualis, szuk scope |
| `FRONTEND_THEME_GUIDE.md` | frontend tema/design alap | aktualis hatter |

## 3. Mi elavult vagy torteneti jellegu

### `README.md`

Korabban munkagepek kozti atadasi jegyzet volt. Frissitve lett projektbelepesi es dokumentacio-navigacios fajlla.

### `MVP_IMPLEMENTATION_PLAN.md`

Hasznos torteneti terv, de tobb benne leirt alap mar megvalosult:
- imports
- finance read
- inventory CRUD/movement/stock
- procurement foundation
- dashboard v1
- catalog/costing alap

Nem szabad napi statuszforraskent hasznalni.

### `MIGRATION_PLAN.md`

Eredeti migration hullamterv. A valos Alembic head mar `019_core_estimated_consumption_audit`, ezert migration igazsagforrasnak a `DATABASE_SYNC_NOTES.md` hasznalando.

### `INITIAL_STRUCTURE.md`

Kiindulo struktura. A valos mappaszerkezet sok ponton letezik, de egyes modulok csak placeholderok. Strukturat ellenorizni kodbol kell, statuszt a `CURRENT_STATUS.md`-bol.

### `IDENTITY_CORE_MODEL_PLAN.md`

Az auth schema/model alaphoz jo hatter, es az Identity/auth MVP statusza frissitve lett. A login/token/guard minimum mar mukodik, de SSO, password reset, refresh token es finomszemcses permission matrix tovabbra sem kesz.

### `PROJECT_DESCRIPTION.md`

Termekviziókent tovabbra is fontos. Viszont endpoint-listai es MVP scope-ja nem aktualis implementacios statusz.

## 4. Implementalt allapot roviden

Mar mukodik:
- master data read
- import upload/parse/batch detail
- POS CSV fallback es normalized POS ingestion
- API/CSV dedupe key
- finance transaction read es POS/supplier invoice tranzakciok
- inventory item CRUD
- inventory movement write/read
- actual stock levels
- theoretical stock read szerzodes
- procurement supplier es purchase invoice alap
- purchase invoice posting
- catalog product/ingredient read-write alap
- recipe/BOM adatmodell
- estimated COGS es margin szamitas
- estimated consumption audit trail POS fogyas magyarazathoz
- Business Dashboard v1 es drill-down endpointok
- basket-pair / receipt drill-down read model

Reszletek: [CURRENT_STATUS.md](CURRENT_STATUS.md).

## 5. Felkesz vagy hianyos reszek

### Kritikus
- nincs finomszemcses role based authorization minden modulra
- valodi kasszakod/SKU mapping nincs
- product_name alapu matching kockazatos

### Fontos, de nem azonnali core blocker
- FIFO costing nincs, csak elokeszitesi alapok
- weather impact nincs implementalva
- Flow event management nincs implementalva
- production batch workflow nincs
- PDF szamla workflow nincs
- finance write workflow nincs

### Placeholder
- backend `events` router
- backend `production` router
- frontend events oldalak
- frontend production oldalak
- `BusinessComparisonPage`
- `InventoryTable` komponens
- altalanos loading/error komponensek jelenleg null komponensek

## 6. Ismert ellentmondasok

### 1. Modul mappa letezik, de funkcio nem

Az `events` es `production` modulok backendben es frontendben is latszanak, de tobb fajl placeholder. Az `identity` modul MVP szinten mar implementalt.

Dokumentacios szabaly:
- mappa vagy ORM model letezese nem jelent kesz funkciot
- csak bekotott router + use case + teszt + frontend flow utan mondjuk kesznek

### 2. Theoretical stock vs estimated stock quantity

Van `GET /api/v1/inventory/theoretical-stock`, de a teljes theoretical engine meg nincs kesz.

Kozben a POS ingestion csokkentheti az `inventory_item.estimated_stock_quantity` erteket, es ezt mar `estimated_consumption_audit` sorok magyarazzak.

Ertelemszeru kulonbseg:
- `theoretical-stock` endpoint = jovobeli estimated/theoretical read contract
- `estimated_consumption_audit` = POS fogyasbol szarmazo estimated stock csokkenes magyarazata, nem actual movement
- `estimated_stock_quantity` = jelenlegi becsult keszletmezo

Kovetkezo feladat:
- theoretical quantity es variance tiszta bekotese

### 3. Profit / margin jelentese

Dashboard profit jelenleg controlling jellegu:
- revenue - posted financial outflow

Estimated margin:
- revenue - estimated COGS

Nem teljes szamviteli profit, es nem FIFO COGS.

Dokumentacios szabaly:
- dashboardon es doksiban mindig jelezni kell, hogy actual, estimated vagy derived metrika.

### 4. Dashboard sample/reference szohasznalat

Regebbi dokumentumokban meg elojohet, hogy dashboard sample vagy reference volt. Aktualis allapot:
- Business Dashboard v1 valos backend read modellel mukodik
- nem sample oldal

### 5. Migration terv vs valos migration allapot

`MIGRATION_PLAN.md` eredeti tervet tartalmaz. Valos allapot:
- Alembic head: `019_core_estimated_consumption_audit`
- igazsagforras: `DATABASE_SYNC_NOTES.md`

### 6. MVP scope vs mar implementalt szeletek

Az eredeti MVP dokumentum tobb eleme meg tervkent ir le olyat, ami mar reszben vagy teljesen megvan. Emiatt napi prioritasra a `ROADMAP.md` hasznalando.

## 7. Dokumentacio frissitesi szabaly

Minden erdemi fejlesztes utan:

1. `CURRENT_STATUS.md`
   - implementalt / felkesz / hianyzo reszek frissitese
   - uj endpointok es frontend oldalak
   - uj kockazatok

2. `ROADMAP.md`
   - kovetkezo prioritas ujrarendezese
   - ne maradjon benne mar elvegzett feladat aktiv kovetkezokent

3. `DATABASE_SYNC_NOTES.md`
   - uj migration
   - Alembic head
   - futtatott tesztek

4. Tematikus direction dokumentum
   - csak ha az adott domain iranya is valtozik

## 8. Feature kesz definicio

Egy feature csak akkor tekintheto kesznek, ha mindegyik feltetel teljesul:
- backend endpoint letezik es be van kotve
- application use case implementalt
- domain szabalyok ervenyesulnek, nem csak adatrokzites tortenik
- integration teszt van ra
- frontend flow hasznalja
- dashboardbol vagy mas relevans UI-bol elerheto
- dokumentacio frissitve van

Ez a szabaly kulonosen fontos a placeholder moduloknal. Mappa, ORM model, route helye vagy frontend oldal fajl letezese onmagaban nem jelent kesz feature-t.

## 9. Nem osszekeverheto fogalmak

Ezeket a dokumentacioban es UI-szovegekben is kovetkezetesen kulon kell tartani:
- a dashboard profit nem konyvelesi profit
- az estimated stock nem actual stock
- a POS mapping nem stabil SKU mapping
- a theoretical stock endpoint nem kesz theoretical stock engine

Ha uj feature erinti ezeket, a response schema, UI label, tooltip es dokumentacio is jelezze, hogy actual, estimated, derived vagy import-derived adatrol van szo.

## 10. Fejlesztesi dontesi sorrend

Ha ket dokumentum ellentmond:

1. Kod es tesztek tenyleges allapota
2. `DATABASE_SYNC_NOTES.md` DB/migration kerdesben
3. `CURRENT_STATUS.md` funkcionális allapotban
4. `ROADMAP.md` kovetkezo prioritasban
5. Tematikus direction dokumentumok
6. Torteneti tervek (`MVP_IMPLEMENTATION_PLAN.md`, `MIGRATION_PLAN.md`, `INITIAL_STRUCTURE.md`)

Ez a sorrend tartja egyben a dokumentaciot es a fejlesztest.
