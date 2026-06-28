# Codex Handoff - 2026-06-28

Ez a handoff a BizTracker fejlesztes uj gepen torteno folytatasahoz keszult.
A cel nem kiserleti playground, hanem lezart, uzletileg hasznalhato elemzo
alkalmazas.

## Repo allapot

- Workspace: `C:\BizTracker\BizTracker-v1`
- Branch: `main`
- Remote: `origin https://github.com/levke998/BizTracker-v1.git`
- Atadas szerinti utolso ismert commit: `7e76984 inventory + stat v1/dashboard 2.0`
- A repo aktualis iranya: Dashboard 2.0, statisztikai/data science alapok,
  forecast/weather/ML elokeszites

## Munkaszabalyok

- Nem hagyunk felkesz blokkot.
- Egy blokk akkor zart, ha backend, frontend, teszt es dokumentacio is kesz.
- Clean Code, SOLID, OOP es modularis felelossegek kotelezok.
- Ticket import jelenleg jegelve, amig nincs konkret export/API dontes.
- A dashboard a termek lelke, nem admin felulet es nem egyszeru mutatogyujtemeny.

## Lezart fo allapot

### Inventory variance/action control

Lezart kontrollfolyamatok:
- hianyzo ar gyorsjavitas
- recept hiba kontroll
- mapping hiba kontroll
- kimaradt beszerzesi szamla kontroll
- fizikai kontroll okok: `waste`, `breakage`, `spoilage`, `theft_suspected`

### Dashboard 2.0 Statistics Quality v1

Kesz payload blokk: `statistics_quality`.

Tartalma:
- POS sor-, kosar-, aktiv nap- es lefedettsegi mintameret
- napi bevetel atlag, median, P25, P75, P90, P95
- kosarertek atlag, median, P25, P75, P90, P95
- `quality_level`: `strong`, `usable`, `limited`, `insufficient`
- `amount_basis = gross`, `amount_origin = actual`

### Dashboard 2.0 Statistics v1.1

Kesz bovites ugyanebben a blokkban:
- naptari napi `rolling_points`
- 7 napos rolling atlag es mozgo median napi bevetelre/kosarertekre
- trendirany, trendstabilitas, trendvaltozas, volatilitas
- outlier/import kontroll flag-ek
- termek- es kategoriakereslet median/P90/P95 percentilisek
- keszletforgas-readiness jelzes

### Dashboard 2.0 Statistics v1.2

Kesz elso insight interpretation layer:
- `statistics_quality.insights` backend read-model
- priorizalt vezetoi ertelmezes adatminoseg, trend, outlier/import kontroll,
  keresleti percentilis es keszletforgas-readiness jelekbol
- minden insight: `code`, `severity`, `category`, `title`, `summary`,
  `recommendation`, `confidence`, `priority_score`, `source_layer`
- frontend kiemelt insight kartyak a statisztikai dashboard blokkon belul
- Dashboard topbaron belul kesz az `Attekintes` / `Professzionalis` nezeti UX
  elso szelete: az attekintes vezeto pulzust es dontesi jelzest ad, a
  professzionalis mod megnyitja a readiness, drill-down, weather/forecast,
  kosar es koltseg melyitest

## Fejlesztoi kornyezet ezen a gepen

User PATH-ba kerult:
- `C:\Program Files\Git\cmd`
- `C:\Users\ADMIN\AppData\Local\Programs\Python\Python312`
- `C:\Users\ADMIN\AppData\Local\Programs\Python\Python312\Scripts`
- `C:\Users\ADMIN\AppData\Local\OpenAI\Codex\runtimes\cua_node\1b23c930bdf84ed6\bin`

Backend venv:
- `backend\.venv`
- telepitve: backend runtime/dev dependencies, `pytest`, `black`

Docker jelenleg nem erheto el ezen a gepen, ezert teljes integration kapu csak
Docker telepites/PATH utan futtathato.

## Aktualis validacio

Sikeres:
- `backend\.venv\Scripts\python.exe -m black --check ...analytics... test_analytics_dashboard_api.py`
- `backend\.venv\Scripts\python.exe -m compileall backend\app\modules\analytics`
- `backend\.venv\Scripts\python.exe -m pytest backend\tests\unit -q` -> `41 passed`
- `backend\.venv\Scripts\python.exe -m pytest backend\tests\integration\test_analytics_dashboard_api.py -q` -> `25 passed`
- frontend TypeScript check
- frontend Vite build, Dashboard chunk kb. `86.36 kB`
- `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\validate.ps1 -SkipIntegration`

Nem futott:
- teljes backend integration, mert Docker nem erheto el

## Kovetkezo javasolt zart blokk

Keszletforgas read-model:
- Statistics v1.2 insight layer es dashboard nezeti UX mar kesz elso szeletben
- kovetkezo lepes a POS keresleti percentilis + production recipe + inventory
  movement actual osszekotese
- Gourmand es Flow kozos analytics mag, specifikus uzleti insightokkal

Utana:
1. Inventory turnover read-model
2. Baseline forecast savos predikcioval
3. Weather decision support
4. Flow analytics melyites
5. ML/szimulacios reteg feature-ready read-modellekkel
