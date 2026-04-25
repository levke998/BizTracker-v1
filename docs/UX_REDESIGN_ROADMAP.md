# BizTracker UX Redesign Roadmap

Ez a dokumentum a BizTracker kovetkezo frontend/UX iranyat rogziti. Celja, hogy a felulet ne admin panelnek hasson, hanem magyar nyelvu, letisztult, dontestamogato business alkalmazasnak.

Kapcsolodo dokumentumok:
- [CURRENT_STATUS.md](CURRENT_STATUS.md)
- [ROADMAP.md](ROADMAP.md)
- [DASHBOARD_DIRECTION.md](DASHBOARD_DIRECTION.md)
- [FRONTEND_THEME_GUIDE.md](FRONTEND_THEME_GUIDE.md)
- [INVENTORY_DIRECTION.md](INVENTORY_DIRECTION.md)

## 1. Alapelv

A BizTracker nem admin nezetre epul. A frontend fo szerepe:
- gyors uzleti attekintes
- KPI-k es diagramok ertelmezheto megjelenitese
- drill-down az adatforrasig
- operativ rogzites ott, ahol az uzleti folyamat ezt indokolja

A technikai eredet es lineage fontos, de nem nyers fejlesztoi valtozonevkent jelenik meg. A user ne lasson olyan szovegeket, mint:
- `derived_actual`
- `recipe_or_unit_cost`
- `import_derived`
- `source POS rows`
- `records`

Ezek helyett emberi, magyar feliratokat kell hasznalni, kontextustol fuggoen:
- "Importalt eladasi adat"
- "Becsult receptkoltseg"
- "Penzugyi tranzakcio"
- "Nyugtasor"
- "Forrasadat"

## 2. Nyelv es szovegezesi szabaly

A fo nyelv magyar.

Elvaras:
- minden lathato frontend szoveg magyarul legyen
- ahol magyar szoveg van, legyen helyes ekezet
- ne legyen angol-magyar keveredes
- a technikai enumok es belso kodok kapjanak magyar label mappinget
- tooltip es segedszoveg csak akkor legyen, ha valodi dontesi segitseget ad

Nem elsodleges most:
- teljes tobbnyelvu i18n rendszer
- nyelvvalto gomb

Kesobbi opcio:
- ha a magyar UI stabil, bevezethetunk i18n csomagot, de most a magyar business UX a prioritas.

## 3. App shell es header

### Sidebar

A bal felso markajelzes legyen:
- minimalista `Activity` ikon
- `BizTracker` felirat
- lila/kek/pink fade accent
- feher egyszeru szoveg helyett markas, de nem tul csicsas logo-kompozicio

Logo koncepcio:
- ikon: lucide `Activity`
- forma: kis lekerekitett ikonkeret vagy standalone vonalikon
- szin: lila -> magenta -> cyan finom atmenet
- felirat: `BizTracker`
- hangulat: premium, minimal, business analytics

Asset koncepcio:
- [assets/biztracker-logo-concept.svg](assets/biztracker-logo-concept.svg)

A "Internal operations workspace" felirat helyett:
- "Üzleti iránytű két vállalkozáshoz"

Sidebarba keruljon:
- aktualis datum
- bejelentkezett felhasznalo roviden
- kilepes gomb magyarul

Keruljon ki:
- `Business read model`
- `BizTracker Admin`
- `Theme direction`
- fejlesztoi/admin jellegu footer szoveg

### Topbar / Header

Maradjon sticky, de:
- legyen nagyobb opacity
- ne olvadjon ossze a tartalommal gorgeteskor
- ne legyen tul alacsony kontrasztu uveghatas

Dashboardon a header tartalma:
- cim: `Dashboard`
- scope valto: `Összesített`, `Flow`, `Gourmand`
- idoszak szuro
- export gomb

Keruljon ki:
- `BizTracker Internal Platform`
- hosszu leiro subtitle: "Overall, Flow and Gourmand..."
- kulon business read model chip

## 4. Navigacio

A menupontok kapjanak minimalista ikonokat a pottyok helyett.

Javasolt menustruktura:
- Dashboard
- Katalogus
  - Termekek
  - Alapanyagok
- Beszerzes
  - Beszallitok
  - Szamlak
- Penzugy
- Import
- Demo kassza
- Torzsadatok

Inventory kulon menu jelenleg tul admin jellegu, ezert kikerul.

Az inventory funkciok a Katalogusba epuljenek be:
- inventory items -> alapanyag/termek torzsadatok
- movements -> alapanyag vagy termek reszleteknel mozgasnaplo
- stock levels -> katalogus alapanyag/termek keszletpanel
- theoretical stock -> becsult keszlet, fogyasi audit, varhato elteres panel

Elv:
- ne legyen duplikalt funkcio
- ahol a katalogus mar megoldja az inventory item karbantartast, ott ne legyen kulon inventory item menu
- ami hianyzik, az uzleti logika szerint keruljon a katalogus reszleteibe

## 5. Dashboard KPI irany

Fo csempek:
- Bevetel
- Kiadas
- Profit

Masodik sor:
- Tranzakciok
- Atlagos kosarertek
- Atlagos kosarmennyiseg

Ne legyen kulon fo KPI:
- Estimated COGS
- Gross margin %
- Profit margin

Ezek kapcsolodo alertekkent jelenjenek meg:
- Profit csempen: becsult arres profit
- Bevetel csempen: tranzakcioszam vagy atlagos kosarertek
- Kiadas csempen: legnagyobb koltsegtipus vagy beszerzesi arany

KPI csempe hover:
- ne takarodjon ki
- ne fedje el rosszul a tobbi elemet
- ha tooltip kell, stabilan, olvashatoan jelenjen meg

## 6. Forgalmi diagram

Ez a dashboard egyik legfontosabb eleme, ezert kulon fejlesztesi szelet.

Cel:
- egyertelmu forgalomalakulas
- interaktiv tooltip
- jol mukodo idoszak szuro
- negativ tartomany kezelese kiadas/profit eseten

Javitando:
- `Today` ne ures diagramot adjon, ha van mai adat
- valoszinuleg timezone vagy napi bucket csuszas van
- `Grouped by day` ne fix szoveg legyen

Uj idoszak presetek:
- 1 ora
- 6 ora
- 12 ora
- Ma
- Het
- Honap
- 30 nap
- Ev
- Egyedi

Adaptiv grain:
- 1 ora: perc vagy 5 perces bucket
- 6/12 ora: ora
- Ma: ora
- Het: nap vagy nap+ora
- Honap: nap
- Ev: honap

Diagram elvaras:
- X tengelyen datum/ido
- Y tengelyen osszeg
- tooltip kurzorra:
  - idopont
  - bevetel
  - kiadas
  - profit
- magyar label
- interaktiv legenda
- a kiadas mehet negativ tartomanyba

## 7. Beveteli megoszlas es drill-down

`Revenue mix / Category breakdown` lista helyett:
- donut vagy kordiagram
- mertekvalto:
  - ertek alapjan
  - mennyiseg alapjan

Drill-down viselkedes:
1. kategoria szeletre kattintas
2. a diagram animaltan atvalt adott kategorian beluli termekmegoszlasra
3. termekre kattintas
4. a reszletes nyugtasorok ugyanabban a csempeben, a diagram alatt jelennek meg

Ne tortenjen:
- ne nyiljon lent kulon, nagy altalanos drill-down blokk
- ne legyen "Source POS rows for this product" angol felirat

Magyar szoveg pelda:
- "Kategoria megoszlas"
- "Termekek a kategoriaban"
- "Kapcsolodo nyugtasorok"

## 8. Top termekek

A jelenlegi vizualis irany tetszik, ezt erdemes erositeni.

Feladat:
- tobb fade/glow accent hasznalata
- 1., 2., 3. hely ikon/badge
- kategoria szuro
- magyar feliratok

Torolni vagy atirni:
- `POS import derived revenue and quantity`
- `6 records · import_derived`

Javasolt magyar szoveg:
- "Legjobban teljesito termekek"
- "Bevetel es mennyiseg alapjan"
- "6 nyugtasor alapjan"
- "Importalt eladasi adat"

## 9. Koltsegkontroll

A koltsegkontroll maradhat listas, mert itt a lista audit es reszletezo szerepe hasznos.

Elvaras:
- magyar feliratok
- nyers transaction type helyett label
- osszeg, darabszam, forras erthetoen

Pelda:
- `supplier_invoice` -> "Beszerzesi szamla"
- `manual_expense` -> "Kezi koltsegrogzites"
- `pos_sale` ne jelenjen meg koltseg oldalon

## 10. Basket analysis

Feladat:
- lista maradhat
- sorra kattintva a reszletek mellette jelenjenek meg kulon csempeben
- fix magassagu, gorgetheto reszletkartya
- a kartya nyujthatja az oldalt lefele, de ne torje szet a fo listat

Magyar szoveg:
- "Egyutt vasarolt termekek"
- "Kosarparok"
- "Kapcsolodo nyugtak"

Minden scope-ban mukodjon:
- Összesített
- Flow
- Gourmand

## 11. Design irany

Megtartando:
- sotet premium alap
- lila/magenta/cyan fade
- gombok glow/fade hatasa
- letisztult kartyaalapu visual system

Erositando:
- fade accent border fontos csempeken
- aktiv tabok finom gradienttel
- chart focus glow
- minimal shine effekt nehany kiemelt kartya szelen
- tobb szines adatvizualizacio, nem csak egyhangú sotet tablazatok

Mozgas:
- lassu, smooth, nem hivalkodo
- nem eroforras-igenyes
- `prefers-reduced-motion` tamogatassal

Kerulendo:
- tul sok animacio egyszerre
- admin dashboard erzet
- tul zsufolt ikonhasznalat
- dekoracio, amely nem segiti az ertelmezest

## 12. Catalog UX es Inventory osszevezetes

Catalog csempe hiba:
- ha egy csempe nyilik, csak az nyiljon
- a tobbi kartya pozicioja igazodjon hozza
- ne nyiljanak uresen mas kartyahelyek

Katalogusba beepul:
- keszletallapot
- mozgasnaplo
- becsult keszlet
- fogyasi audit
- theoretical stock/variance irany, ahol relevans

Kivetel:
- kulon Inventory Overview
- Inventory Items
- Inventory Movements
- Stock Levels
- Theoretical Stock kulon menu

## 13. Uj relevans dashboard kimutatasok

Javasolt kovetkezo diagramok:

1. Forgalmi hoterkep
   - napok es orak szerint
   - mutatja, mikor eros a forgalom

2. Fizetesi mod megoszlas
   - keszpenz
   - kartya
   - SZEP kartya

3. Kosarertek eloszlas
   - nem csak atlag
   - latszik, milyen savokban vasarolnak

4. Kategoria trend
   - mely kategoriak nonek vagy esnek
   - elozo idoszakhoz kepest

5. Gyenge termekek / figyelendo termekek
   - alacsony forgalom
   - gyenge arres
   - nagy koltseg vagy alacsony eladas

6. Keszletkockazat panel
   - gyorsan fogyó alapanyagok
   - alacsony becsult keszlet
   - recept alapu varhato fogyas

7. Flow-specifikus kesobbi kimutatas
   - esemenyenkenti bevetel
   - esemenyenkenti profit
   - esemeny elotti/utani forgalmi hatas

8. Gourmand-specifikus kesobbi kimutatas
   - idojaras-erzekeny kategoriak
   - fagylalt/sutemeny/sos termek trend
   - termekkategoria profitabilitas

## 14. Megvalositasi roadmap

### 1. Nyelvi es UI-szoveg alapozas

Cel:
- magyar, ekezetes, business-barát frontend

Feladat:
- frontend lathato szovegek atirasa
- technical label mapper bevezetese
- source layer es transaction type label mapping
- angol subtitle-ok torlese vagy magyaritasa

### 2. App shell es navigacio

Cel:
- admin/platform erzet csokkentese

Feladat:
- sidebar logo Activity ikonnal
- datum/felhasznalo/kilepes sidebarba
- header egyszerusitese
- menuikonok
- Catalog lenyilo menu
- Inventory kulon menuk kivetele

### 3. Dashboard header es KPI refactor

Cel:
- dontestamogato dashboard elso kepernyo

Feladat:
- scope/period/export headerbe
- scope valto csempe eltavolitasa
- KPI csempek ujrarendezese
- hover/tooltip javitas

### 4. Forgalmi diagram ujraepitese

Cel:
- megbizhato, interaktiv forgalmi trend

Feladat:
- Today bug javitasa
- 1/6/12 oras presetek
- adaptiv bucket/grain
- tooltip
- X/Y tengely
- negativ tartomany

### 5. Kategoria es termek drill-down

Cel:
- lista helyett vizualis, egy csempen beluli elemzes

Feladat:
- donut chart
- ertek/mennyiseg valto
- kategoria -> termek drill-down
- termek -> nyugtasor reszlet ugyanazon csempen belul

### 6. Top termekek es basket UX

Cel:
- vizualisan eros, de tiszta uzleti elemzes

Feladat:
- helyezes ikonok
- kategoria szuro
- technikai label torles
- basket reszletkartya kulon panelben

### 7. Catalog + Inventory osszevezetes

Cel:
- kevesebb admin menu, tobb logikus uzleti felulet

Feladat:
- katalogus csempe nyitas javitasa
- keszletpanel bevezetese
- mozgasnaplo bevezetese
- fogyasi audit bevezetese
- inventory menuk kivezetese

### 8. Uj dashboard kimutatasok

Cel:
- tobb valodi uzleti elemzesi lehetoseg

Feladat:
- fizetesi mod megoszlas
- forgalmi hoterkep
- kosarertek eloszlas
- kategoria trend
- keszletkockazat

## 15. Definition of Done UX szeletekre

Egy UX szelet akkor kesz, ha:
- magyarul, ekezetesen jelenik meg
- nincs nyers valtozonev a UI-ban
- mobil/tablet/desktop mereten hasznalhato
- nem duplikal admin funkciot
- adatforras es metrika jelentese ertheto
- tesztelve van builddel
- erintett dokumentacio frissult

