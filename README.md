# BizTracker

BizTracker egy belso uzleti elemzo es controlling rendszer a `Gourmand` es a `Flow Music Club` mukodesenek kovetesere.

Fo irany: biztonsagos CSV importokra epulo, forrasadatig visszakovetheto dashboard es operativ dontestamogatas. Nem realtime kassza API-ra epulunk.

## Dokumentacios rend

Fejlesztes elott ezt olvasd:

1. [docs/ROADMAP.md](docs/ROADMAP.md) - egyseges sorvezeto, kesz/felkesz/kritikus/jovo feladatok.
2. [docs/DOMAIN_MODEL.md](docs/DOMAIN_MODEL.md) - Gourmand, Flow, inventory, procurement, recept es dashboard domain.
3. [docs/DATA_PIPELINE.md](docs/DATA_PIPELINE.md) - CSV-first import, dedupe, mapping, PDF szamla pipeline.
4. [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - modularis monolit, clean architecture, frontend/backend felelossegek.
5. [docs/OPERATIONS.md](docs/OPERATIONS.md) - futtatas, migration, teszt, dokumentaciofrissites.

Dokumentacios index: [docs/DOCUMENTATION_STATUS.md](docs/DOCUMENTATION_STATUS.md).

## Gyors lokal futtatas

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

## Jelenlegi fokusz

1. CSV-first import pipeline tokeletesitese.
2. POS/SKU/barcode mapping es missing mapping quarantine.
3. Gourmand recept, stock es inventory accounting-ready erosites.
4. Beszerzesi szamla PDF review workflow.
5. Flow event rendszer es Event elemzo befejezese.
6. Dashboard tovabbi uzlet-specifikus melyitese.
