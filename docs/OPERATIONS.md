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

## Adatbazis es migration

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

Legutobb dokumentalt teljes integration allapot: `94 passed`.

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
