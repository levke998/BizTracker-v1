# BizTracker Operations

Ez a dokumentum a fejlesztoi futtatas, validacio es dokumentaciofrissites rovid operacios helye.

## Lokal futtatas

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

## Windows fejlesztoi PATH es venv

Az uj gepen a fejlesztoi alap user PATH-ba kerult:

```text
C:\Program Files\Git\cmd
C:\Users\ADMIN\AppData\Local\Programs\Python\Python312
C:\Users\ADMIN\AppData\Local\Programs\Python\Python312\Scripts
C:\Users\ADMIN\AppData\Local\OpenAI\Codex\runtimes\cua_node\1b23c930bdf84ed6\bin
```

Meglevo Codex/terminal folyamat nem mindig veszi at azonnal a friss user PATH-ot;
uj terminalban kell latszania. A backendhez repo-lokalis virtualenv keszult:

```powershell
cd C:\BizTracker\BizTracker-v1
backend\.venv\Scripts\python.exe -m pip install -e "backend[dev]" black
```

A `scripts\validate.ps1` eloszor ezt a venv Pythont hasznalja, ha letezik.
Docker nelkuli gyors kapu:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\validate.ps1 -SkipIntegration
```

## Adatbazis es migration

Uj fejlesztoi gep, Docker/PostgreSQL es gepkozi DB snapshot:
[DEVELOPMENT_SETUP.md](DEVELOPMENT_SETUP.md).

Aktualis Alembic allapot ellenorzese:

```powershell
cd C:\BizTracker\backend
python -m alembic current
```

Migration futtatasa:

```powershell
cd C:\BizTracker\backend
python -m alembic upgrade head
```

Szabalyok:
- schema valtozasnal migration kotelezo
- migrationt kezzel ellenorizni kell
- demo/test seed nem szennyezheti a valos Gourmand/Flow adatokat
- source reference es dedupe key nem torolheto el

## Tesztek

Teljes lokalis validacio a repository gyokerebol:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\validate.ps1
```

Az integration suite dedikalt, minden futasnal ujraletrehozott
`biztracker_test` adatbazison fut. A helyi uzleti snapshoton integration tesztet
nem futtatunk.

Backend integration tesztek:

```powershell
cd C:\BizTracker\backend
python -m pytest tests/integration -q
```

Kritikus tesztteruletek:
- imports
- finance mapping
- catalog
- inventory movements/stock/estimated consumption
- procurement purchase invoices/posting
- analytics dashboard
- events
- weather
- identity/auth

Legutobb dokumentalt teljes integration allapot: `172 passed`.

Legutobbi celzott validacio:
- Event ticket actual lefedettseg frontend szelet utan:
  - `npm.cmd run build` -> sikeres
  - fo JS chunk: kb. `224.27 kB`, `DashboardPage`: kb. `79.19 kB`, `EventsPage`: kb. `38.94 kB`
- Flow POS fogyasztasi kontrollkartya utan:
  - `npm.cmd run build` -> sikeres
  - fo JS chunk: kb. `224.27 kB`, `DashboardPage`: kb. `79.19 kB`, `EventsPage`: kb. `35.61 kB`
- Flow POS-ticket korrekcio utan:
  - `python -m pytest C:\BizTracker\backend\tests\integration\test_events_api.py -q` -> `9 passed`
  - `python -m compileall C:\BizTracker\backend\app\modules\events C:\BizTracker\backend\tests\integration\test_events_api.py` -> sikeres
  - `npm.cmd run build` -> sikeres
  - fo JS chunk: kb. `224.27 kB`, `DashboardPage`: kb. `76.01 kB`, `EventsPage`: kb. `35.61 kB`
  - DB tesztmaradvany takaritas: `test-integration` business unit `1` torolve, `python -m scripts.clean_demo_data` dry-run nem jelzett torlendo demo rekordot
- Flow penzugyi mix dashboard szelet utan:
  - `npm.cmd run build` -> sikeres
  - fo JS chunk: kb. `224.27 kB`, `DashboardPage`: kb. `77.37 kB`, `EventsPage`: kb. `35.61 kB`
- Flow dashboard penzugyi/event szerepszethuzas utan:
  - `npm.cmd run build` -> sikeres
  - fo JS chunk: kb. `224.27 kB`, `DashboardPage`: kb. `76.26 kB`, `EventsPage`: kb. `35.61 kB`
- Frontend route-level lazy loading utan:
  - `npm.cmd run build` -> sikeres
  - fo JS chunk: kb. `224.27 kB`, `DashboardPage`: kb. `78.01 kB`, `EventsPage`: kb. `35.61 kB`
- Flow/Gourmand dashboard osszehangolas utan:
  - `npm.cmd run build` -> sikeres
  - megjegyzes: Vite chunk size warning maradt, build hiba nelkul
- Flow event insight panel frontend szelet utan:
  - `npm.cmd run build` -> sikeres
- Flow event osszehasonlito frontend szelet utan:
  - `npm.cmd run build` -> sikeres
- Flow event dontestamogato profit mutatok utan:
  - `python -m pytest C:\BizTracker\backend\tests\integration\test_events_api.py -q` -> `9 passed`
  - `python -m compileall C:\BizTracker\backend\app\modules\events C:\BizTracker\backend\tests\integration\test_events_api.py` -> sikeres
  - `npm.cmd run build` -> sikeres
- PDF adapter + recipe overview + Flow platform fee szelet utan:
  - `python -m pytest C:\BizTracker\backend\tests\integration\test_procurement_purchase_invoices_api.py -q` -> `15 passed`
  - `python -m pytest C:\BizTracker\backend\tests\integration\test_production_recipes_api.py -q` -> `4 passed`
  - `python -m pytest C:\BizTracker\backend\tests\integration\test_events_api.py -q` -> `9 passed`
  - `python -m compileall C:\BizTracker\backend\app\modules\events C:\BizTracker\backend\app\modules\production C:\BizTracker\backend\app\modules\procurement C:\BizTracker\backend\tests\integration\test_events_api.py C:\BizTracker\backend\tests\integration\test_production_recipes_api.py` -> sikeres
  - `npm.cmd run build` -> sikeres
  - procurement/production/event integration tesztek parhuzamos futtatasa a kozos test adatbazis miatt interferalhat; kulon futtatva zold
- DB tesztadat takaritas utan:
  - torolve: `test-integration` business unit `1`, teszt kategoriak `5`, inaktiv demo termekek `4`, `Other Unit Supplier ...` teszt suppliers `13`; a kesobbi integration tesztfuttatas utan ujra letrejott `2` supplier es `1` test business unit is torolve
  - ellenorzes: business unitok csak `gourmand`, `flow`; test unit `0`; inaktiv termek `0`; suppliers `0`; recipe/recipe_version/recipe_ingredient `0`
  - `python -m scripts.clean_demo_data` dry-run mar csak `0` torlendo demo rekordot jelez a megtartott real import alap mellett
- PDF extraction confidence szelet utan:
  - `python -m pytest C:\BizTracker\backend\tests\integration\test_procurement_purchase_invoices_api.py -q` -> `15 passed`
  - `python -m compileall C:\BizTracker\backend\app\modules\procurement C:\BizTracker\backend\tests\integration\test_procurement_purchase_invoices_api.py` -> sikeres
  - `npm.cmd run build` -> sikeres
- PDF szamla text-layer elotoltes szelet utan:
  - `python -m pytest C:\BizTracker\backend\tests\integration\test_procurement_purchase_invoices_api.py -q` -> `15 passed`
  - `python -m pytest C:\BizTracker\backend\tests\integration\test_procurement_purchase_invoice_posting_api.py -q` -> `4 passed`
  - `python -m compileall C:\BizTracker\backend\app\modules\procurement C:\BizTracker\backend\tests\integration\test_procurement_purchase_invoices_api.py` -> sikeres
  - `npm.cmd run build` -> sikeres
  - a procurement integration tesztek parhuzamos futtatasa a kozos test adatbazis miatt interferalhat; kulon futtatva zold
- Beszerzesi szamla AFA forrasjeloles szelet utan:
  - `python -m pytest C:\BizTracker\backend\tests\integration\test_procurement_purchase_invoices_api.py -q` -> `14 passed`
  - `python -m compileall C:\BizTracker\backend\app C:\BizTracker\backend\tests` -> sikeres
  - `npm.cmd run build` -> sikeres
- Recept verzio UX szelet utan:
  - `python -m pytest C:\BizTracker\backend\tests\integration\test_production_recipes_api.py -q` -> `4 passed`
  - `npm.cmd run build` -> sikeres
- Recept sablonos inditas frontend szelet utan:
  - `python -m pytest C:\BizTracker\backend\tests\integration\test_production_recipes_api.py -q` -> `4 passed`
  - `npm.cmd run build` -> sikeres
- Recept readiness missing VAT gyorsjavito szelet utan:
  - `python -m pytest C:\BizTracker\backend\tests\integration\test_production_recipes_api.py -q` -> `4 passed`
  - `npm.cmd run build` -> sikeres
- Termek profit/margin reporting szelet utan:
  - `python -m pytest C:\BizTracker\backend\tests\integration\test_analytics_dashboard_api.py -q` -> `23 passed`
  - `python -m compileall C:\BizTracker\backend\app\modules\analytics` -> sikeres
  - `npm.cmd run build` -> sikeres
- POS AFA readiness/coverage dashboard szelet utan:
  - `python -m pytest C:\BizTracker\backend\tests\integration\test_analytics_dashboard_api.py -q` -> `23 passed`
  - `python -m compileall C:\BizTracker\backend\app\modules\analytics` -> sikeres
  - `npm.cmd run build` -> sikeres
- Recept/production AFA costing szelet utan:
  - `python -m pytest C:\BizTracker\backend\tests\integration\test_production_recipes_api.py -q` -> `4 passed`
  - `python -m compileall C:\BizTracker\backend\app\modules\production C:\BizTracker\backend\tests\integration\test_production_recipes_api.py` -> sikeres
  - `npm.cmd run build` -> sikeres
- POS revenue derived AFA dashboard szelet utan:
  - `python -m pytest C:\BizTracker\backend\tests\integration\test_analytics_dashboard_api.py -q` -> `23 passed`
  - `python -m compileall C:\BizTracker\backend\app\modules\analytics C:\BizTracker\backend\tests\integration\test_analytics_dashboard_api.py` -> sikeres
  - `npm.cmd run build` -> sikeres
- Analytics backend es Dashboard frontend refaktor lezarasa utan:
  - analytics unit tesztek -> `32 passed`
  - `python -m pytest C:\BizTracker\backend\tests\integration -q` -> `157 passed`
  - `python -m compileall C:\BizTracker\backend\app\modules\analytics` -> sikeres
  - `npm.cmd run build` -> sikeres (`DashboardPage` chunk kb. `81.38 kB`)
- Event analytics summary backend read-model utan:
  - `python -m compileall C:\BizTracker\backend\app\modules\events` -> sikeres
  - `python -m pytest C:\BizTracker\backend\tests\integration\test_events_api.py -q` -> `10 passed`
  - `npm.cmd run build` -> sikeres (`EventsPage` chunk kb. `35.91 kB`)
- Flow event koltsegsorok v1 utan:
  - `python -m alembic upgrade head` -> `034_core_inventory_variance_threshold -> 035_core_event_cost_line`
  - `python -m compileall C:\BizTracker\backend\app\modules\events C:\BizTracker\backend\migrations\versions\20260508_035_core_event_cost_line.py` -> sikeres
  - `python -m pytest C:\BizTracker\backend\tests\integration\test_events_api.py -q` -> `11 passed`
  - `npm.cmd run build` -> sikeres (`EventsPage` chunk kb. `39.57 kB`)
- Flow performer settlement szabalyok v1 utan:
  - `python -m alembic upgrade head` -> `035_core_event_cost_line -> 036_core_event_performer_settlement_type`
  - `python -m compileall C:\BizTracker\backend\app\modules\events C:\BizTracker\backend\migrations\versions\20260508_036_core_event_performer_settlement_type.py` -> sikeres
  - `python -m pytest C:\BizTracker\backend\tests\integration\test_events_api.py -q` -> `12 passed`
  - `npm.cmd run build` -> sikeres (`EventsPage` chunk kb. `40.71 kB`)
- Inventory akciojavaslatok v1 utan:
  - nincs uj migration
  - `python -m compileall C:\BizTracker\backend\app\modules\inventory` -> sikeres
  - `python -m pytest C:\BizTracker\backend\tests\integration\test_inventory_variance_action_suggestions_api.py -q` -> `2 passed`
  - `python -m pytest C:\BizTracker\backend\tests\integration\test_inventory_movement_api.py C:\BizTracker\backend\tests\integration\test_inventory_variance_period_comparison_api.py -q` -> `11 passed`
  - `npm.cmd run build` -> sikeres
- Inventory akciojavaslat review v1 utan:
  - `python -m alembic upgrade head` -> `036_core_event_performer_settlement_type -> 037_core_inventory_variance_action_review`
  - `python -m alembic current` -> `037_core_inventory_variance_action_review (head)`
  - `python -m compileall C:\BizTracker\backend\app\modules\inventory C:\BizTracker\backend\migrations\versions\20260508_037_core_inventory_variance_action_review.py` -> sikeres
  - `python -m pytest C:\BizTracker\backend\tests\integration\test_inventory_variance_action_suggestions_api.py -q` -> `3 passed`
  - `python -m pytest C:\BizTracker\backend\tests\integration -q` -> `163 passed`
  - `npm.cmd run build` -> sikeres (`TheoreticalStockPage` chunk kb. `27.05 kB`)
- Inventory akciojavaslat gyors celpont v1 utan:
  - nincs uj migration
  - `python -m compileall C:\BizTracker\backend\app\modules\inventory` -> sikeres
  - `python -m pytest C:\BizTracker\backend\tests\integration\test_inventory_variance_action_suggestions_api.py -q` -> `3 passed`
  - `python -m pytest C:\BizTracker\backend\tests\integration -q` -> `163 passed`
  - `npm.cmd run build` -> sikeres (`TheoreticalStockPage` chunk kb. `27.53 kB`)
- Inventory akciojavaslat fokuszparameterek utan:
  - nincs uj migration
  - `python -m compileall C:\BizTracker\backend\app\modules\inventory` -> sikeres
  - `python -m pytest C:\BizTracker\backend\tests\integration\test_inventory_variance_action_suggestions_api.py -q` -> `3 passed`
  - `python -m pytest C:\BizTracker\backend\tests\integration -q` -> `163 passed`
  - `npm.cmd run build` -> sikeres (`CatalogIngredientsPage` chunk kb. `21.43 kB`, `TheoreticalStockPage` chunk kb. `27.88 kB`)
- Inventory akciojavaslat fokusz banner utan:
  - nincs uj migration
  - `python -m compileall C:\BizTracker\backend\app\modules\inventory` -> sikeres
  - `python -m pytest C:\BizTracker\backend\tests\integration\test_inventory_variance_action_suggestions_api.py -q` -> `3 passed`
  - `python -m pytest C:\BizTracker\backend\tests\integration -q` -> `163 passed`
  - `npm.cmd run build` -> sikeres (`CatalogIngredientsPage` chunk kb. `21.89 kB`, `TheoreticalStockPage` chunk kb. `28.39 kB`)
- Inventory akciojavaslat visszaut/fokusz torles utan:
  - nincs uj migration
  - `python -m compileall C:\BizTracker\backend\app\modules\inventory` -> sikeres
  - `python -m black --check C:\BizTracker\backend\app\modules\inventory\application\queries\list_variance_action_suggestions.py C:\BizTracker\backend\tests\integration\test_inventory_variance_action_suggestions_api.py` -> sikeres
  - `python -m pytest C:\BizTracker\backend\tests\integration\test_inventory_variance_action_suggestions_api.py -q` -> `3 passed`
  - `python -m pytest C:\BizTracker\backend\tests\integration -q` -> `163 passed`
  - `npm.cmd run build` -> sikeres (`CatalogIngredientsPage` chunk kb. `22.50 kB`, `TheoreticalStockPage` chunk kb. `28.84 kB`)
- Git es smoke zaras:
  - `git show-ref --head --dereference` -> `main`, `origin/main` es `origin/HEAD` ugyanarra a `094fb9e...` commitra mutat
  - `git fsck --no-progress` -> exit code 0; sok dangling tree latszik, de hianyzo/korrupt kotelezo objektum nincs
  - `git fetch --dry-run origin` -> sikeres; a korabbi `bad object refs/remotes/origin/main` hiba nem reprodukalhato
  - `npm.cmd run preview -- --host 127.0.0.1 --port 4173` + `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000` mellett:
    - `GET http://127.0.0.1:4173/inventory/theoretical-stock?business_unit_id=smoke` -> 200, React root HTML elerheto
    - `GET http://127.0.0.1:8000/openapi.json` -> 200, tartalmazza a `/api/v1/inventory/variance-action-suggestions` endpointot
    - `GET http://127.0.0.1:8000/api/v1/inventory/variance-action-suggestions?days=30` -> 200
  - in-app browser vizualis smoke nem futott le: a browser runtime inicializalas `failed to write kernel assets` hibat adott, ezert csak HTTP smoke eredmeny kerult rogzitesre
- Inventory hianyzo ar gyorsjavitas v1 utan:
  - nincs uj migration
  - `python -m black --check C:\BizTracker\backend\app\modules\inventory\application\queries\list_variance_action_suggestions.py C:\BizTracker\backend\tests\integration\test_inventory_variance_action_suggestions_api.py` -> sikeres
  - `python -m compileall C:\BizTracker\backend\app\modules\inventory` -> sikeres
  - `python -m pytest C:\BizTracker\backend\tests\integration\test_inventory_variance_action_suggestions_api.py -q` -> `4 passed`
  - `python -m pytest C:\BizTracker\backend\tests\integration -q` -> `164 passed`
  - `npm.cmd run build` -> sikeres (`CatalogIngredientsPage` chunk kb. `24.07 kB`, `TheoreticalStockPage` chunk kb. `28.84 kB`)
- Inventory recept hiba kontroll v1 utan:
  - nincs uj migration
  - `python -m black --check C:\BizTracker\backend\app\modules\inventory\application\queries\list_variance_action_suggestions.py C:\BizTracker\backend\tests\integration\test_inventory_variance_action_suggestions_api.py` -> sikeres
  - `python -m compileall C:\BizTracker\backend\app\modules\inventory` -> sikeres
  - `python -m pytest C:\BizTracker\backend\tests\integration\test_inventory_variance_action_suggestions_api.py -q` -> `5 passed`
  - `python -m pytest C:\BizTracker\backend\tests\integration -q` -> `165 passed`
  - `npm.cmd run build` -> sikeres (`RecipesPage` chunk kb. `28.67 kB`, `TheoreticalStockPage` chunk kb. `28.84 kB`)
  - `git diff --check` -> sikeres, csak meglovo CRLF figyelmeztetesekkel
- Inventory mapping hiba kontroll v1 utan:
  - nincs uj migration
  - `python -m black --check C:\BizTracker\backend\app\modules\inventory\application\queries\list_variance_action_suggestions.py C:\BizTracker\backend\tests\integration\test_inventory_variance_action_suggestions_api.py` -> sikeres
  - `python -m compileall C:\BizTracker\backend\app\modules\inventory` -> sikeres
  - `python -m pytest C:\BizTracker\backend\tests\integration\test_inventory_variance_action_suggestions_api.py -q` -> `6 passed`
  - `python -m pytest C:\BizTracker\backend\tests\integration -q` -> `166 passed`
  - `npm.cmd run build` -> sikeres (`ImportCenterPage` chunk kb. `45.81 kB`, `TheoreticalStockPage` chunk kb. `28.84 kB`)
- Inventory kimaradt beszerzesi szamla kontroll v1 utan:
  - nincs uj migration
  - `python -m black --check C:\BizTracker\backend\app\modules\inventory\application\queries\list_variance_action_suggestions.py C:\BizTracker\backend\tests\integration\test_inventory_variance_action_suggestions_api.py` -> sikeres
  - `python -m compileall C:\BizTracker\backend\app\modules\inventory` -> sikeres
  - `python -m pytest C:\BizTracker\backend\tests\integration\test_inventory_variance_action_suggestions_api.py -q` -> `7 passed`
  - `python -m pytest C:\BizTracker\backend\tests\integration -q` -> `167 passed`
  - `npm.cmd run build` -> sikeres (`InvoicesPage` chunk kb. `37.82 kB`, `TheoreticalStockPage` chunk kb. `28.84 kB`)
- Inventory fizikai kontroll okok v1 utan:
  - nincs uj migration
  - `python -m black --check C:\BizTracker\backend\app\modules\inventory\application\queries\list_variance_action_suggestions.py C:\BizTracker\backend\tests\integration\test_inventory_variance_action_suggestions_api.py` -> sikeres
  - `python -m compileall C:\BizTracker\backend\app\modules\inventory` -> sikeres
  - `python -m pytest C:\BizTracker\backend\tests\integration\test_inventory_variance_action_suggestions_api.py -q` -> `11 passed`
  - `python -m pytest C:\BizTracker\backend\tests\integration -q` -> `171 passed`
  - `npm.cmd run build` -> sikeres (`TheoreticalStockPage` chunk kb. `31.50 kB`)
- Dashboard 2.0 Statistics Quality v1 utan:
  - nincs uj migration
  - `python -m black --check C:\BizTracker\backend\app\modules\analytics\domain\entities\dashboard_snapshot.py C:\BizTracker\backend\app\modules\analytics\presentation\schemas\dashboard.py C:\BizTracker\backend\app\modules\analytics\infrastructure\repositories\statistics_analytics_builder.py C:\BizTracker\backend\app\modules\analytics\infrastructure\repositories\sqlalchemy_analytics_repository.py C:\BizTracker\backend\tests\integration\test_analytics_dashboard_api.py` -> sikeres
  - `python -m compileall C:\BizTracker\backend\app\modules\analytics` -> sikeres
  - `python -m pytest C:\BizTracker\backend\tests\integration\test_analytics_dashboard_api.py -q` -> `24 passed`
  - `python -m pytest C:\BizTracker\backend\tests\integration -q` -> `172 passed`
  - `npm.cmd run build` -> sikeres (`DashboardPage` chunk kb. `84.15 kB`)
- Dashboard 2.0 Statistics v1.1 utan:
  - nincs uj migration
  - Windows user PATH javitva Git/Python/npm iranyba; backend `.venv` letrehozva
  - `backend\.venv\Scripts\python.exe -m black --check ...analytics... test_analytics_dashboard_api.py` -> sikeres
  - `backend\.venv\Scripts\python.exe -m compileall backend\app\modules\analytics` -> sikeres
  - `backend\.venv\Scripts\python.exe -m pytest backend\tests\unit -q` -> `41 passed`
  - `backend\.venv\Scripts\python.exe -m pytest backend\tests\integration\test_analytics_dashboard_api.py -q` -> `25 passed`
  - frontend `tsc --noEmit` -> sikeres
  - frontend `vite build` -> sikeres (`DashboardPage` chunk kb. `86.36 kB`)
  - `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\validate.ps1 -SkipIntegration` -> sikeres
  - teljes integration nem futott ezen a gepen, mert Docker nem erheto el
- Dashboard 2.0 Statistics v1.2 insight interpretation layer elso szelet utan:
  - nincs uj migration
  - `backend\.venv\Scripts\python.exe -m black backend\app\modules\analytics\domain\entities\dashboard_snapshot.py backend\app\modules\analytics\presentation\schemas\dashboard.py backend\app\modules\analytics\infrastructure\repositories\statistics_analytics_builder.py backend\tests\integration\test_analytics_dashboard_api.py` -> sikeres
  - `backend\.venv\Scripts\python.exe -m pytest backend\tests\integration\test_analytics_dashboard_api.py -q` -> `25 passed`
  - `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\validate.ps1 -SkipIntegration` -> sikeres (`41 passed`, frontend build-check sikeres)
  - `npm.cmd run build` -> sikeres (`DashboardPage` chunk kb. `87.25 kB`)
- Dashboard 2.0 Attekintes/Professzionalis UX elso szelet utan:
  - nincs uj migration
  - `backend\.venv\Scripts\python.exe -m pytest backend\tests\integration\test_analytics_dashboard_api.py -q` -> `25 passed`
  - frontend `npm.cmd run build:check` -> sikeres (`DashboardPage` chunk kb. `87.62 kB`)
- POS import file-set sorrend flake javitas utan:
  - `python -m pytest C:\BizTracker\backend\tests\integration\test_imports_api.py::test_parse_gourmand_pos_sales_file_set_uses_summary_categories -q` -> `1 passed`
- POS import stuck-batch es duplicate alias regresszio utan:
  - `python -m pytest C:\BizTracker\backend\tests\integration\test_imports_api.py -q` -> `15 passed`
  - `python -m compileall C:\BizTracker\backend\scripts\recover_import_batch.py C:\BizTracker\backend\app\modules\imports C:\BizTracker\backend\app\modules\pos_ingestion` -> sikeres
- POS alias review es manual mapping elso szelet utan:
  - `python -m pytest C:\BizTracker\backend\tests\integration\test_imports_api.py -q` -> `12 passed`
  - `python -m pytest C:\BizTracker\backend\tests\integration\test_imports_finance_mapping_api.py -q` -> `6 passed`
  - `npm.cmd run build` -> sikeres
  - parhuzamosan futtatott import es finance mapping tesztek a kozos integration test business unit miatt osszeakadhatnak; kulon futtatva mindketto zold

## Import helyreallitas

Ha egy POS import technikai hiba miatt `parsing` allapotban ragad, eloszor mindig ellenorizni kell, hogy nincs-e mar rogzitett staging sor vagy penzugyi tranzakcio. Az erre keszult script csak akkor enged helyreallitast, ha a batch meg ures.

Dry-run:

```powershell
cd C:\BizTracker\backend
python -m scripts.recover_import_batch --batch-id <batch-uuid>
```

Helyreallitas parse + finance mapping futtatassal:

```powershell
cd C:\BizTracker\backend
python -m scripts.recover_import_batch --batch-id <batch-uuid> --apply --map-finance
```

Elv:
- csak `parsing` vagy `failed` statuszu, sor/tranzakcio nelkuli batch javithato igy
- ha barmilyen staging sor vagy finance tranzakcio mar letezik, a script megall
- sikeres futas utan ellenorizni kell a `DUPLICATE_DEDUPE_KEYS` kimenetet

## Weather automation

Backendben van built-in weather automation. Kulon OS scheduler csak fallback/uzemeltetesi opcio.

Hasznos parancsok:

```powershell
cd C:\BizTracker\backend
python -m scripts.sync_weather --days-back 2 --json
python -m scripts.sync_weather_forecast --forecast-days 7 --json
python -m scripts.backfill_import_weather
```

Elv:
- dashboard request ne hivjon kulso weather providert
- import vagy event coverage hiany potolhato, de provider hiba nem buktathat importot
- event performance ellenorzesnel a profit margin, koltsegarany es jegy/bar mix csak az aktualis read-model allapotot jeloli; ticket actual hianyaban nincs jegybevetel becsles, a POS idoblokk kizarolag bar/fogyasztasi bevetel

## Dokumentaciofrissitesi szabaly

Dokumentaciot akkor kell frissiteni, ha:
- adatfolyam valtozik
- API contract valtozik
- domain fogalom valtozik
- roadmap/prioritas valtozik
- dashboard KPI jelentese valtozik
- actual/estimated/derived hatar valtozik

Hova irjunk:
- [ROADMAP.md](ROADMAP.md): prioritas, kesz/felkesz/kovetkezo lepes
- [DOMAIN_MODEL.md](DOMAIN_MODEL.md): domain szabaly, fogalom, uzleti modell
- [DATA_PIPELINE.md](DATA_PIPELINE.md): import, CSV, PDF, dedupe, mapping
- [ARCHITECTURE.md](ARCHITECTURE.md): technikai szerkezet es kodminosegi irany
- [OPERATIONS.md](OPERATIONS.md): futtatas, teszt, migration, uzemeltetes

## Branch es munkaelv

- nem torlunk vagy revertalunk user munkat egyeztetes nelkul
- unrelated valtozasokat nem keverunk feature-be
- minden fejlesztesnel a roadmap aktualis P0/P1 iranyai elveznek elonyt
