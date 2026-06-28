# Dashboard 2.0 Analytics Strategy

Ez a dokumentum rogziti, hogy a Dashboard 2.0 nem mellekfunkcio, hanem a
BizTracker termekmagja. A cel olyan uzleti elemzo es dontestamogato rendszer,
amely valos adatminosegi kapukkal, statisztikai modellekkel, vizualis
ertelmezessel es kesobbi prediktiv/ML reteggel segiti a vezetest.

## Termekelv

- A dashboard nem admin lista es nem statisztikai mutato-gyujtemeny.
- Minden mutato egy uzleti kerdesre valaszoljon: mi tortent, miert tortent,
  mennyire biztos, es mi legyen a kovetkezo lepes.
- A frontend nem szamol uj uzleti igazsagot; a dashboard backend read-modelt
  jelenit meg, magyar, business-barat szoveggel.
- A statisztikai mutatok csak kontextusban hasznosak: median, percentilis,
  rolling average vagy volatilitas mellett mindig kell ertelmezes, confidence
  vagy kovetkezo cselekves.
- A Gourmand es Flow specifikus modellek kozos analytics magra epuljenek,
  de az uzleti kerdesek masok: Gourmandnal demand, recept, keszlet, weather;
  Flownal event, ticket actual, bar/POS fogyasztas, profit es kapacitas.

## Analytics reteg

Leiro statisztika:
- napi bevetel, kosarertek, termek- es kategoriakereslet atlag/median/P25/P75/P90/P95
- rolling average es mozgo median idosorok
- eloszlas es volatilitas jelzes, nem csak egyszeru atlag

Kovetkeztetesi alap:
- outlier es import-hiany jelzes
- mintaerosseg, aktiv nap, POS sor, kosar es mapping/readiness coverage
- weather/category/product kapcsolat csak mintaszammal es adatminoseggel
- korrelacio nem okozatisag; minden kapcsolat magyarazati jelzes, nem bizonyitek

Prediktiv alap:
- baseline forecast pesszimista/realista/optimista savval
- weather-normal es aktualis forecast alapu demand modositok
- keszletforgas es recept alapu elokeszitesi javaslat
- Monte Carlo csak konkret dontesi helyzetben: keszlethiany kockazat,
  elokeszitesi mennyiseg, event profit vagy heti cash-flow range

## Vizualizacios elv

- A vezeto ne adatot banyasszon, hanem dontesi jelzest kapjon.
- Minden diagramnak legyen cime, uzleti ertelme es kiemelt jelzese.
- A statisztikai panel mutassa, hogy a kovetkeztetes mennyire tamaszkodhato.
- A melyebb/professzionalis nezet elfogadhato a dashboardon belul, de az elso
  kepernyo mindig adjon gyors uzleti pulzust.
- Latvanyos vizualizacio csak akkor ertek, ha nem rejti el a source lineage-et,
  missing data allapotot es confidence jelzest.

## Nezeti modell

Az elso dashboardon beluli nezeti bontas kesz:
- `Attekintes`: vezetoi pulzus, KPI-k, trend, statisztikai insightok, uzleti fokusz,
  scope-specifikus osszefoglalo, top termek/keszlet kockazat
- `Professzionalis`: az attekinto reteg mellett adatminosegi readiness, mapping/AFA
  coverage, kategoria drill-down, traffic heatmap, weather/forecast, kosar- es
  kiadasmelyites

Ez nem kulon statisztika oldal: ugyanaz a Dashboard 2.0 felulet kap ket
olvasasi modot. A szamitas tovabbra is backend read-model, a frontend csak
prioritast es melyseget valt.

## Kesz definicio Dashboard 2.0 szeletre

Egy dashboard analytics szelet akkor kesz, ha:
- backend read-model/API schema adja a szamitasokat
- frontend megjeleniti, nem ujraszamolja
- van celzott backend teszt
- dokumentalt a domain jelentese, adatforrasa es bizonytalansaga
- actual/derived/estimated/forecast hatar egyertelmu
- Gourmand/Flow kozos mag vagy specifikus elteres tisztan latszik
- a kovetkezo prediktiv/ML reteghez nem zavaros, hanem hasznalhato feature-t ad

## Kovetkezo zart szeletek

1. Statistics v1.2 - Insight interpretation layer:
   - kesz elso szelet: top 3 uzleti insight backendbol
   - kesz elso szelet: trend + outlier + demand percentilis magyarazat egy kozos dontesi panelben
   - kesz elso UX szelet: altalanos es professzionalis dashboard nezeti bontas

2. Inventory turnover read-model:
   - product/category demand percentilis + recept + inventory movement osszekotes
   - forgasi sebesseg, napnyi keszlet, hiany kockazat
   - Gourmand elokeszitesi es beszerzesi dontes tamogatasa

3. Baseline forecast:
   - napi bevetel es kategoriakereslet savos becsles
   - quality/confidence gating a `statistics_quality` alapjan
   - forecast nem egyetlen pontszam, hanem sav es magyarazat

4. Weather decision support:
   - weather cache + historikus POS kapcsolat
   - cukraszdai kategoriak idojaras-erzekenysege
   - rovid tavu forecast es 17-30 napos bizonytalanabb weather-normal jelzes

5. Flow analytics deepening:
   - event profit, ticket actual coverage, POS bar/fogyasztas ritmus
   - event weather/context es performer/koltseg mix
   - Flow dashboardon osszesito, Event elemzoben mely drill-down
