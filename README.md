# BizTracker

BizTracker egy belso uzleti elemzo es controlling rendszer a `Gourmand` es a `Flow Music Club` mukodesenek kovetesere. A cel nem egy egyszeru CRUD admin, hanem KPI-, grafikon-, drill-down- es adatforras-kovetesi fokuszu alkalmazas.

## Dokumentacios rend

Fejlesztes elott ezeket olvasd ebben a sorrendben:

1. [docs/CURRENT_STATUS.md](docs/CURRENT_STATUS.md) - tenyleges jelenlegi allapot, implementalt es hianyzo reszek.
2. [docs/ROADMAP.md](docs/ROADMAP.md) - aktiv fejlesztesi irany es kovetkezo fokuszok.
3. [docs/DOCUMENTATION_STATUS.md](docs/DOCUMENTATION_STATUS.md) - melyik dokumentum mire valo, mi elavult, milyen ellentmondasok vannak.
4. [docs/DATABASE_SYNC_NOTES.md](docs/DATABASE_SYNC_NOTES.md) - Alembic head, DB-validacio es tesztelt migracios allapot.

Termek- es architektura-hatter:
- [PROJECT_DESCRIPTION.md](PROJECT_DESCRIPTION.md) - eredeti termekvizió es hosszabb tavu scope.
- [docs/BUSINESS_DIRECTION.md](docs/BUSINESS_DIRECTION.md) - uzleti elemzesi celok.
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - modularis monolit, Clean Architecture irany.
- [docs/ACCOUNTING_AND_CONTROLLING_MODEL.md](docs/ACCOUNTING_AND_CONTROLLING_MODEL.md) - actual vs estimated controlling modell.

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

A projekt mar tul van az alap scaffoldon: mukodik a POS/import -> finance -> analytics/dashboard tobb szelete, a catalog/costing alap, az inventory CRUD/movement/stock read, valamint a procurement invoice posting alap. A kovetkezo fejlesztesi iranyt a [docs/ROADMAP.md](docs/ROADMAP.md) vezeti.
