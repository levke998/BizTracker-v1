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
