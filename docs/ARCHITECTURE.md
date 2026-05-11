# BizTracker Architecture

Ez a dokumentum a jelenlegi technikai irany rovid igazsagforrasa. A reszletes termekiranyt a [ROADMAP.md](ROADMAP.md), a domain donteseket a [DOMAIN_MODEL.md](DOMAIN_MODEL.md), az import adatfolyamot a [DATA_PIPELINE.md](DATA_PIPELINE.md) vezeti.

## Alapdontes

A BizTracker modularis monolit:
- backend: FastAPI, SQLAlchemy 2, Alembic
- frontend: React, TypeScript, Vite, TanStack Query
- adatbazis: PostgreSQL celarchitektura
- mukodes: CSV-first ingestion, adatbazis-alapu analytics/read model

Nem microservice iranyban haladunk. A modulhatarokat tisztan tartjuk, de a gyors fejlesztes es egyszerubb uzemeltetes miatt egy alkalmazason belul maradunk.

## Backend retegzes

Modulon beluli celminta:

```text
backend/app/modules/<module>/
  presentation/
    api/
    schemas/
    dependencies.py
  application/
    commands/
    queries/
    services/
    dto/
  domain/
    entities/
    value_objects/
    repositories/
    services/
  infrastructure/
    orm/
    repositories/
    mappers/
```

Felelossegek:
- `presentation`: HTTP, request/response schema, auth dependency
- `application`: use case, tranzakcio-koordinacio, domain/repository orchestration
- `domain`: uzleti szabaly, entitas, value object, repository interface
- `infrastructure`: ORM, repository implementacio, kulso provider

Szabaly:
- domain nem ismeri az ORM-et
- use case nem legyen nyers CRUD script
- import, procurement, inventory es analytics kozt explicit boundary legyen
- actual, estimated es derived fogalmak kulon tipusban/mezoiben jelenjenek meg

## Backend modulok

Aktualis modulok:
- `identity`: login, current user, token
- `master_data`: business unit, location, unit, category, product
- `imports`: file upload, batch, parse, rows, errors, import profile
- `pos_ingestion`: normalizalt receipt boundary, demo/API adapter szerep, POS product alias/read API
- `finance`: financial transaction read es source mapping
- `catalog`: product es ingredient catalog, recipe/costing read-write szeletek
- `inventory`: item, movement, stock level, estimated consumption audit
- `procurement`: supplier, purchase invoice, invoice posting
- `production`: recipe costing/readiness read-side es kesobbi production/batch folyamatok
- `events`: Flow event planner, event performance, weather coverage
- `weather`: Szolnok observation es forecast cache
- `analytics`: dashboard es drill-down read-modelek
- `demo_pos`: fejlesztoi tesztkliens

## Analytics es statisztikai modellek

Az analytics modul feladata nem csak aggregalt KPI, hanem dontestamogato read-model is.

Elvek:
- leiro statisztika backend/read-model oldalon keszuljon, frontend csak megjelenit
- predikcios es statisztikai mezok mindig tartalmazzanak adatminosegi vagy readiness jelzest
- forecast/predikcio ne legyen osszekeverve actual adattal
- korrelacio es Monte Carlo ne fusson requestenkent nagy nyers adaton; kesobb cache-elt read-model vagy batch szamitas kell
- kis mintaszamu kovetkeztetes UI-ban csak figyelmezteto jelzes lehet, nem erosen fogalmazott ajanlas

Kezdeti technikai irany:
- egyszeru statisztikai segedfuggvenyek: median, P25/P75/P90/P95 percentile, szoras, histogram bucket, outlier flag
- idosoros aggregacio nap/ora/het napja szerint, 7/14 napos rolling average es mozgo median mezokkel
- market basket read-model support, confidence es lift metrikakkal
- anomalia detektalas elso korben szabaly/statisztikai baseline, kesobb cserelheto ML modellre
- predikcios savok egyszeru baseline modellel induljanak, kesobb cserelheto model service mogott
- regression/Bayes/scenario modellek kulon application service-kent epuljenek, hogy ne terheljek tul a dashboard repositoryt
- Monte Carlo kulon application service legyen, explicit bemenettel es reprodukalhato seed/opcio mezokkel
- ML modellekhez kesobb model registry vagy legalabb verziozott model metadata kell: model name, version, trained_at, feature window, data quality score

## Frontend felepites

Aktualis szerkezet:

```text
frontend/src/
  app/
  routes/
  modules/
  services/
  shared/
  styles/
```

Modul minta:

```text
src/modules/<module>/
  pages/
  api/
  hooks/
  types/
  components/
```

Frontend szabalyok:
- a frontend a megjelenitesert es interakcioert felel
- nagyobb uzleti szamitas backend/read-model oldalon legyen
- query cache TanStack Query-ben
- technikai enumokhoz magyar label mapping kell
- admin CRUD helyett KPI, chart, drill-down es review workflow legyen a fo UX
- Inventory kulon admin menu helyett a Katalogus/Beszerzes/Dashboard kontextusaban jelenjen meg, ahol lehet

## Data boundary

CSV-first irany:

```text
raw file -> import_file -> import_batch -> import_row -> domain mapping -> read model
```

Realtime POS API nem fo cel. A `pos_ingestion` endpoint maradhat teszt- es adapter boundary, de a termekfejlesztes a CSV import stabilitasara epul.

POS mapping boundary:
- parse utan a catalog sync hozza letre vagy frissiti a POS product alias rekordokat
- alias tabla nem helyettesiti a product torzsadatot, hanem source lineage es review alap
- jovahagyas nelkuli alias `auto_created` allapotban marad, igy kesobb dashboard/filter szinten megkulonboztetheto

## Teljesitmeny es optimalizalas

Elv:
- dashboard request ne vegezzen kulso provider hivast
- weather es forecast cache hatterben frissuljon
- import parse es mapping legyen idempotens
- nagy listakhoz backend filter/pagination irany kell, ha az adatmennyiseg no
- frontend ne toltson le felesleges reszleteket a fold feletti dashboardhoz
- nagy frontend oldalak route-level lazy loadinggal toltodnek, hogy a dashboard es event modulok ne noveljek minden oldal elso JS bundle-jet

## Production recipe boundary

Az elso production clean architecture szelet kesz:
- domain: recept costing/readiness entitasok es allapotok
- application: `ListRecipesQuery`
- application command: `SaveActiveProductRecipeCommand`
- domain repository contract: `RecipeRepository`
- infrastructure: `SqlAlchemyRecipeRepository`
- presentation: `/api/v1/production/recipes`

A catalog termeklista recept/onkoltseg read oldala ezt a production read modellt hasznalja. Igy a stock hiany, missing recipe es missing cost szabaly nem szorodik szet router helper fuggvenyekbe.

Frontend elso szelet:
- `src/modules/production/api/productionApi.ts`
- `src/modules/production/hooks/useRecipes.ts`
- `src/modules/production/pages/RecipesPage.tsx`
- route: `/production/recipes`

Ez munkanezet, nem dashboard: a cel a recept readiness es hianyallapotok kezelese.

Write-side elso refaktor:
- a catalog product create/update mar nem kozvetlenul kezeli az aktiv receptverziok inaktivalasat es az uj `recipe_ingredient` sorokat
- a catalog presentation retege `RecipeDraft`-ot keszit es production application commandot hiv
- a command validal, a repository ment; a HTTP hibara forditas a catalog presentation retegben marad
- onallo endpoint is kesz: `PUT /api/v1/production/products/{product_id}/recipe`
- a frontend Recept readiness oldal mar ezt az endpointot hasznalja szerkeszteskor; a catalog mar nem az egyetlen receptiras entrypoint
- a frontend work queue gyorsjavitasai nem kerulik meg a modulhatarokat: recept mentese production API, alapanyag ar/keszlet potlas catalog ingredient API, majd query invalidalas utan uj read-model

## Kodminoseg

Kotelezo elvek:
- OOP, ahol domain objektum vagy use case indokolja
- SOLID, kulonosen single responsibility es dependency inversion
- kis, tesztelheto use case osztalyok/fuggvenyek
- repository interface a domain/application hataron
- nincs hidden magic number uzleti szabalyban
- konfiguralt vagy adatbazisban tarolt szabaly, ha uzletileg valtozhat
- hianyos adat nem okozhat nem kezelt kivetelt

## Migration es DB

Alembic revisionok a `backend/migrations/versions` alatt vannak. A DB allapotot kodolasi munka elott ellenorizni kell, ha schema valtozas erintett.

Szabaly:
- migrationt kezzel ellenorizni
- seed/demo adat ne szennyezze a valos Gourmand/Flow adatokat
- source reference es dedupe kulcs megorzese kritikus
- invoice/POS/import source lineage nem torolheto el business adatokbol

## Tesztelesi elv

Integration teszt kell minden olyan szeletre, amely:
- importot parse-ol vagy domain mappinget vegez
- penzugyi tranzakciot hoz letre
- inventory movementet vagy estimated consumptiont erint
- dashboard read-modelt valtoztat
- event performance vagy procurement posting viselkedest modosit

Legutobb dokumentalt backend integration allapot: `94 passed`.
