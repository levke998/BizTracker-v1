# BizTracker Roadmap

Ez a dokumentum a projekt rovid tavu, kozep tavu es kesobbi iranyat foglalja ossze. A cel az, hogy a fejlesztes ne essen szet kulonallo feature-okra, hanem a projektleirasban vallalt celok fele haladjon.

Kapcsolodo dokumentumok:
- [CURRENT_STATUS.md](C:\BizTracker\docs\CURRENT_STATUS.md)
- [PROJECT_DESCRIPTION.md](C:\BizTracker\PROJECT_DESCRIPTION.md)
- [BUSINESS_DIRECTION.md](C:\BizTracker\docs\BUSINESS_DIRECTION.md)
- [DATABASE_SYNC_NOTES.md](C:\BizTracker\docs\DATABASE_SYNC_NOTES.md)
- [DASHBOARD_DIRECTION.md](C:\BizTracker\docs\DASHBOARD_DIRECTION.md)
- [INVENTORY_DIRECTION.md](C:\BizTracker\docs\INVENTORY_DIRECTION.md)
- [THEORETICAL_STOCK_PREPARATION.md](C:\BizTracker\docs\THEORETICAL_STOCK_PREPARATION.md)

## 1. Mar megvan

### Foundation
- backend / frontend alap
- migrations
- env config
- reference data bootstrap

### Imports
- upload
- parse
- rows / errors detail
- pos_sales profil
- finance mapping MVP

### Finance
- transaction read API
- frontend read oldal

### Inventory
- item CRUD alap
- movement write/read
- actual stock level read
- theoretical stock readiness read
- frontend read oldalak
- frontend item create/edit/archive flow
- frontend movement create flow

### Procurement
- supplier foundation
- supplier list/create backend
- supplier list/create frontend
- purchase invoice foundation
- purchase invoice list/create backend
- purchase invoice list/create frontend

## 2. Aktiv irany

Most az inventory modul van a legjobb allapotban ahhoz, hogy egy rendezett, vegiggondolt operativ es controlling resz alapja legyen.

Ezert a kozvetlen fokusz:
- procurement invoice -> inventory / finance kapcsolat
- inventory es controlling kapcsolat tisztan tartasa
- a dashboard-first vegcel tudatos epitese
- a source-data workflow erosites

## 3. Kovetkezo 5 konkret implementacios lepes

1. procurement invoice -> inventory / finance mapping foundation
   - manual purchase invoice adatok bekotese
   - inventory novekedes es penzugyi oldal kozelitese
   - kesobbi PDF workflow elokeszitese
   - fo gepen elso lepes: `alembic upgrade head`, lasd [DATABASE_SYNC_NOTES.md](C:\BizTracker\docs\DATABASE_SYNC_NOTES.md)
   - kod szinten elkezdve: purchase invoice posting endpoint, finance transaction mapping, inventory movement mapping, frontend post action
   - hatralevo: fo gepes DB migration es integration test futtatas

2. identity auth MVP
   - login
   - token flow
   - route/API guardok

3. theoretical stock valodi becslesi alapjanak letetele
   - recipe / BOM minimum
   - consumption rules
   - actual vs estimated variance alap

4. inventory valuation elokeszitese
   - costing szemlelet
   - FIFO kompatibilis adatelokeszites

5. overall / business dashboard valodi adatos szelete
   - revenue / cost / profit alap KPI
   - drill-down kompatibilis read modellek
   - kod szinten elkezdve: `GET /api/v1/analytics/dashboard`, scope-ok, period presetek, frontend business dashboard v1
   - kod szinten elkezdve: category -> product es expense type -> transaction drill-down endpointok
   - hatralevo: fo gepes DB integration test es source-row szintu drill-down endpointok

## 3/A. Strategiai hangsulyok

A kovetkezo fejleszteseknel ezeket a hangsulyokat tartsuk szem elott:
- a rendszer fo celja a `Gourmand` es a `Flow` uzleti elemzese
- az inventory fontos, de nem vegcel, hanem controlling alapreteg
- sales-driven szemlelet maradjon eros, kulonosen a Gourmand oldalon
- a file import maradjon elso osztalyu workflow, ameddig nincs biztos API kapcsolat
- a vegso UX dashboard, KPI es drill-down alapu rendszer fele haladjon

## 4. Kozep tavu irany

### Inventory / Gourmand
- recipe kezeles
- production alap
- estimated consumption
- actual vs theoretical stock
- sales-driven theoretical stock modell

### Flow
- event alapmodell
- ticket es bar oldali profitabilitas
- performer rule konfiguracio

### Finance
- tovabbi write workflow
- koltseg oldali strukturalt modell
- KPI read modellek

### Dashboard / business analysis
- `Overall` business dashboard
- `Flow Music` business dashboard
- `Gourmand` business dashboard
- drill-down chart es KPI rendszer
- idojaras alapu korrelacios reteg

## 5. Kesobbi irany

- FIFO kompatibilis costing reteg
- inventory valuation
- event settlement finomitas
- analytics dashboardok
- weather es demand alapu predikcio

## 6. Dontesi elvek, hogy ne vesszunk el

Minden kovetkezo implementacios korben tartsuk ezt a sorrendet:

1. domain jelentese legyen tiszta
2. backend read/write szelet legyen stabil
3. frontend csak ezutan epuljon ra
4. actual es estimated retegek ne keveredjenek
5. ne ugorjunk egyszerre tobb modul mely implementaciojaba

## 7. Jelenlegi ajanlott kovetkezo konkret feladat

Ha a kovetkezo kodolas-orientalt lepesrol kell donteni, a legjobb valasztas:
- procurement invoice -> inventory / finance mapping foundation

Ez kozvetlenul segit:
- megalapozni a PDF es manualis beszerzesi workflow-kat
- osszekotni a kiadasi oldalt az inventory novekedessel es a penzuggyel
- jobb alapot adni a FIFO es valuation kovetkezo lepesekhez
