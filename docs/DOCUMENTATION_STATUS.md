# BizTracker Documentation Status

Ez a dokumentum a dokumentacios rend rovid indexe.

## Aktualis dokumentumok

Fejlesztes elott ezt az 5 dokumentumot erdemes nezni:

1. [ROADMAP.md](ROADMAP.md) - egyseges sorvezeto, allapot, prioritas, kovetkezo lepes.
2. [DOMAIN_MODEL.md](DOMAIN_MODEL.md) - Gourmand, Flow, inventory, procurement, costing es dashboard domain szabalyok.
3. [DATA_PIPELINE.md](DATA_PIPELINE.md) - CSV-first import, dedupe, mapping, PDF pipeline es source lineage.
4. [ARCHITECTURE.md](ARCHITECTURE.md) - modularis monolit, clean architecture, backend/frontend felelossegek.
5. [OPERATIONS.md](OPERATIONS.md) - futtatas, migration, teszt es dokumentaciofrissitesi szabaly.

## Mi lett osszevonva

A korabbi sok reszdokumentum tartalma ezekbe kerult:
- business direction, current status, roadmap es presentation status -> `ROADMAP.md`
- accounting, inventory, theoretical stock, catalog/costing es dashboard domain -> `DOMAIN_MODEL.md`
- POS integration, import profiles, weather analytics es database sync notes relevans reszei -> `DATA_PIPELINE.md` es `OPERATIONS.md`
- frontend/UX/theme irany -> `ROADMAP.md` es `ARCHITECTURE.md`
- migration/MVP/initial/identity tervek -> `ARCHITECTURE.md` es `OPERATIONS.md`

## Mi szamit elavultnak

Elavult minden olyan szemlelet, amely:
- realtime kassza API-t tekint fo iranynak
- CSV-t csak fallbackkent kezeli
- demo POS-t valodi kasszahelyettesitokent irja le
- actual es estimated adatot osszemos
- dashboardot admin tablazatok halmazakent kezeli

## Frissitesi szabaly

Ha egy fejlesztes erinti a CSV importot, dashboardot, inventoryt, procurementet, receptet vagy event rendszert, legalabb egy aktualis dokumentumot frissiteni kell.

Dokumentum darabszamot alacsonyan tartjuk. Uj dokumentum csak akkor johet letre, ha:
- tartosan onallo felelossege van
- nem fer ertelmesen az 5 aktualis dokumentum egyikbe sem
- a `DOCUMENTATION_STATUS.md` is frissul vele
