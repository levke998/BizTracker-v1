# BizTracker Roadmap

Ez az egyseges fejlesztesi sorvezeto. A cel nem dokumentumgyujtemeny fenntartasa, hanem valos elorehaladas vezetese egy belso uzleti elemzo es controlling rendszer fele.

## Strategiai dontes

2026-05-04-tol a BizTracker fo adatbeviteli iranya:

```text
biztonsagos CSV import -> validalt staging -> domain mapping -> analytics/read model
```

Nem epulunk realtime kassza API-ra. A kasszaprogram nagyon bizalmas, NAV fele meno adatot kezel, ezert a BizTracker nem ker es nem var realtime adatkapcsolatot. A POS/API endpointok fejlesztoi es kesobbi adapter boundary szerepben maradhatnak, de a termekirany CSV-first.

Kovetkezmeny:
- a CSV import pipeline lesz a legfontosabb adatbizalmi reteg
- minden import legyen visszakeresheto, validalhato es deduplikalt
- a dashboard csak adatbazisba mentett, normalizalt sorokbol dolgozhat
- a kasszaadat hiba, hiany vagy mapping problema nem torheti meg az alkalmazast

## Vegcel

A BizTracker uzleti elemzo rendszer:
- KPI, diagram, trend, drill-down es forrasadatig kovetheto elemzes
- Gourmand-specifikus termek, recept, keszlet, idojaras es kereslet elemzes
- Flow-specifikus event, jegy, bar, performer es event-profit elemzes
- leiro es kovetkeztetesi statisztika dontestamogatashoz: median, szoras, eloszlas, idosor, korrelacio es predikcio
- actual es estimated adatok szigoru szetvalasztasa
- accounting-ready inventory es procurement alapok, de nem teljes konyveloprogram
- penzugyi mutatok egyertelmu netto/brutto/AFA jelolese beveteli es kiadasi oldalon, mert vallalkozoi dontesnel nem mindegy, hogy levonhato AFA-val, brutto cash-flow-val vagy netto koltseggel dolgozunk

Nem cel:
- egyszeru CRUD admin felulet
- realtime kasszafugges
- korai microservice bontas
- feketedobozos ML stabil historikus adat nelkul
- estimated adat actual tenykent kezelese
- statisztikai mutatok oncelu megjelenitese uzleti dontesi kontextus nelkul

## Allapot roviden

Kesz es hasznalhato:
- FastAPI backend, React + TypeScript + Vite frontend
- modularis monolit, tobb modulban clean architecture bontassal
- Alembic migration pipeline
- identity/auth MVP: login, `/me`, token, frontend route guard
- master data read
- CSV import upload, batch, parse, rows, errors
- POS import listan latszik a parse-olt forgalmi csomag idoszaka: elso es utolso eladasi idopont
- POS parser ellenorzi az osszesito es teteles CSV-k metadata idoszak-osszhangjat
- Gourmand POS CSV csomag feldolgozas: osszesito + teteles fajlok
- Flow POS CSV profil ugyanarra a csomaglogikara felkeszitve
- POS import utan kategoria es termek adaptacio
- POS aktualis termekar adaptacio `sale_price_last_seen_at` alapon, import sorrendtol fuggetlenul
- POS source product alias alap: POS termeknev/SKU/barcode kulcs nyilvantartasa mapping reviewhoz
- POS alias sync batch-en beluli deduplikacio: azonos POS source key egy batch-ben egy alias rekord, tobb elofordulas szamlalva
- POS alias review munkalista az Import kozpontban es manual mapping endpoint
- POS recept hiany munkalista az Import kozpontban kasszabol ismert, de recept nelkuli termekekre
- finance mapping POS sorokbol
- financial transaction read
- catalog product/ingredient CRUD, archive szemlelettel
- recipe/BOM adatmodell es catalogon beluli receptadatok
- Termekkatalogusban kulon `Termekek` / `Receptek` nezetvalto elso szelete
- Recept szerkeszto elso validacios UX: kereses, becsult receptkoltseg, duplikalt/hibas sorok mentese elotti jelzese
- Production recipe read API elso clean architecture szelete: domain entitasok, repository contract, SQLAlchemy repository, application query es `/api/v1/production/recipes`
- Catalog termeklista recept/onkoltseg olvasasa mar a production recipe read modellen keresztul tortenik, nem sajat duplikalt costing helperrel
- Production/Recept readiness frontend munkanezet elso szelete: uzletenkenti lista, kereses, missing recipe/missing cost/missing stock/empty recipe/ready szurok, osszetevo reszletek es katalogus visszalepes
- Recept irasi oldal elso production application refaktora: catalog product create/update mar `SaveActiveProductRecipeCommand` use case-en es `RecipeRepository` contracton keresztul ment aktiv receptverziot
- Onallo production recipe write endpoint es frontend szerkesztes elso szelete: `PUT /api/v1/production/products/{product_id}/recipe`, Recept readiness oldali receptnev/kihozatal/osszetevo szerkesztes
- Recept readiness work queue elso gyorsjavito szelete: hiany kategoriakra ugro munkalista gombok, missing cost alapanyag ar potlas, missing/unknown/insufficient stock becsult keszlet potlas a recept reszletekbol
- estimated COGS es margin becsles recept vagy direkt koltseg alapjan
- inventory item, movement, actual stock level
- estimated consumption audit POS fogyas magyarazathoz
- theoretical stock elso uzleti szelet: teoretikus mennyiseg, aktualis beszerzesi ar alapu keszlet ertek, variance statusz es keszleteltĂ©rĂ©s indikĂˇtor
- fizikai keszletszamolas/korrekcio, variance ok-kategoriak, elteres trend, legnagyobb vesztesegu tetelek, HUF becsles es elso anomalia statuszok
- procurement supplier, purchase invoice es invoice posting
- PDF beszerzesi szamla draft upload/list/review/konverzio alap: PDF tarolas, review_required/review_ready/invoice_created statusz, manualis review sorok, netto/AFA/brutto kalkulacio, supplier item alias tanulas es munkalista, vegleges szamla letrehozas posting nelkul
- beszerzesi szamla postingkor a kapcsolt inventory item default beszerzesi koltsege frissul, szamlasor forrassal es frissebb cost vedelmi szaballyal
- Business Dashboard v1 valos adatbol, scope-okkal es drill-downokkal
- weather cache, forecast cache es dashboard weather/forecast read-modelek elso szeletei
- Flow event CRUD, event planner, event performance read-model es event-weather coverage

Felkesz:
- recipe UX, production read-side, production readiness frontend, onallo recept write endpoint, recept save command es elso gyorsjavito work queue szelet kesz, de a teljes tomeges hianykezeles es fejlettebb verzio/publikacio workflow meg nincs kesz
- theoretical stock es inventory controlling alap kesz, periodus-osszehasonlitas, elso HUF alapu dontesi javaslat es uzletenkent mentheto anomalia kuszobok keszek
- FIFO/valuation nem fo MVP irany; Gourmandnal az aktualis, legfrissebb beszerzesi ar alapu teoretikus keszlet ertek a controlling szemlelet
- procurement szamla rogzites es PDF draft upload/list/review/vegleges szamla letrehozas alap van, supplier item alias tanulas elso szeletevel; OCR/adatkinyeres meg nincs
- Flow event settlement lite van, teljes elszamolasi motor nincs
- dashboard eros MVP, de a Gourmand es Flow specifikus dashboardokat melyiteni kell

Kritikus hianyok:
- POS alias tomeges review UX
- missing mapping quarantine import/katalogus munkalista finomitasa
- PDF beszerzesi szamla OCR/adatkinyeresi workflow
- kontrollalt finance/inventory posting teljes brutto/netto/AFA riportolhatosaggal
- beveteli es kiadasi dashboard netto/brutto/AFA jelolese es szamolasi modjai
- receptkezeles teljes workflow: fejlettebb verzio/publikacio szemlelet, recept hiany tomeges muveletek, duplikalt/missing cost munkalistabol inditott gyors javitasok
- inventory controlling tovabbi dontesi javaslatok ok- es item-szintu melyitese
- stabil teszt- es dokumentaciofrissitesi fegyelem minden feature utan

## Prioritasok

### P0 - Iranyrogzites es adatbizalom

1. CSV-first import pipeline megerositese.
2. POS/API szovegek, doksik es UI gondolkodas atallitasa CSV-first szemleletre.
3. POS/SKU/barcode alias modell. Elso backend es frontend review szelet kesz: `pos_product_alias`, read API, manual mapping endpoint, Import kozpont panel.
4. Missing mapping quarantine: amit nem tudunk biztosan termekhez kotni, az ne torzitsa a dashboardot. Elso alap kesz: auto-created alias allapot lathato es jovahagyhato.
5. POS idoszak es dedupe erosites: napi, heti, delben/este ujratoltott csomagoknal csak a hianyzo sorok rogzuljenek.
6. POS import technikai hibakezeles: parse hiba utan rollback + `failed` statusz, es ures beragadt batch helyreallito script. Kesz elso javitas.
7. PDF szamla validacios workflow: parse utan ellenorizheto, javithato, majd jovahagyhato adatok.

### P1 - Gourmand mag

1. Termekkatalogus alatt kulon `Receptek` ful.
2. Receptverzio, hozam, mertekegyseg, osszetevo es koltseg logika tisztitasa.
3. Recipe -> estimated consumption -> theoretical stock osszekotes.
4. Alapanyag es termeknev megfeleltetes erositese, mert beszerzesi szamlan markaneves termeknevek jonnek.
5. Recept -> termek -> eladas netto/brutto/AFA lanc: stock/inventory item AFA kulcsabol es beszerzesi arabol induljon a receptkoltseg, majd termek eladasi oldalon vilagosan latszodjon netto/brutto/AFA es margin.
6. Gourmand dashboard: kategoria, termek, recept, estimated COGS, keszletkockazat, idojaras es elokeszitesi ajanlas.

### P1 - Inventory es procurement

1. Beszerzesi szamla adatmodell brutto/netto/AFA mezokkel.
2. PDF feltoltes elso pipeline:
   - PDF file tarolas: kesz elso szelet
   - OCR/adatkinyeres boundary: draft mezok elokeszitve
   - review dialog: kesz elso manualis szelet
   - felhasznaloi javitas: kesz elso manualis szelet
   - validalas: kesz elso netto/AFA/brutto kalkulacios szelet
   - reviewbol vegleges szamla letrehozas: kesz elso kontrollalt szelet, posting nelkul
   - ismeretlen beszallitoi tetel kezelese: kesz elso szelet, alias tanulassal es reviewbol uj inventory item letrehozassal
   - default cost frissites postingkor: kesz elso szelet, szamlasor forrassal es frissebb cost vedelmi szaballyal
   - posting inventory es finance iranyba
3. Supplier invoice line -> inventory item mapping.
4. Inventory item default AFA kulcs kovetkezetes hasznalata stock, receptkoltseg, beszerzesi szamla review es termek profit kalkulacioban.
5. Aktualis beszerzesi ar, default cost, estimated COGS es keszleten allo penz elkulonitese.
6. Teoretikus keszlet ertek a legfrissebb beszerzesi arbol, FIFO retegezes nelkul.
7. Keszletelteres indikator: recept alapu vart fogyas vs rogzitett actual/korrekcios keszlet.

### P1 - Flow event rendszer

Idozites: a PDF szamla draft/upload elso szelete utan a Flow Business Dashboard beveteli scope pontositas es az Event elemzo kovetkezik, meg az inventory/accounting melyites teljes befejezese elott.

Scope pontositas:
- Flow Business Dashboard = uzleti/beveteli dashboard, Gourmandhoz hasonlo vezetoi szemlelettel
- Event/Esemeny elemzo = event osszesito es osszehasonlito felulet
- event rangsor, legfelkapottabb event, performer bontas es event profit az Event elemzoben van, nem kulon dashboard blokkban

1. Event planner es event analyzer befejezese. Kesz elso UX pontositas: event osszesito kap legfelkapottabb es legnagyobb forgalmu jelzest.
2. Event idosav alapu POS/CSV late-binding stabilizalasa.
3. Ticket es bar revenue szetvalasztasa. Kesz elso szelet: `event_ticket_actual` kulon ticket actual reteg manualis rogziteshez, performance integracioval.
4. Performer share/fixed fee/event cost konfiguralt modell.
5. Flow dashboard ticket/bar mix, kategoria, termek, csucsidok es beveteli trend kontextussal.

### P2 - Dashboard es UX

1. Dashboard legyen a fo termekelmeny, nem admin lista.
2. Tablazatok csak drill-down, audit es validacio szerepben maradjanak.
3. Overall, Gourmand es Flow scope valtas erositese.
4. Kartyak es diagramok a valos uzleti kerdesekre valaszoljanak.
5. Magyar, business-barat szovegek; technikai enumok ne jelenjenek meg nyersen.

### P2 - Statisztika es predikcio

1. Adatminosegi alap: outlier kezeles, import hiba jelzes, mintaszam es mapping/readiness jelzes minden statisztikai kovetkezteteshez.
2. Atlag melle median es percentilisek/kvantilisek: P25, P75, P90, P95 kosarertekre, napi bevetelre, termek darabszamra, event bevetelre.
3. Szoras es eloszlas/hisztogram ott, ahol a szorodas uzleti dontes: napi/oras forgalom, kosarertek, termekkereslet, event teljesitmeny, keszlet variance.
4. Idosoros elemzes: rolling average, mozgo median, trendirany, szezonalitas, het napja, napszak, honap, unnepnap, event-nap es idojaras kontextus.
5. Korrelacio/kovariancia: idojaras-termek, idojaras-kategoria, event-bar fogyasztas; mindig mintaszam, idoszak es adatminoseg jelzessel.
6. Kosar-asszociacio / market basket analysis: support, confidence es lift egyutt vasarolt termekek elemzesere.
7. Anomalia detektalas: szokatlanul magas/alacsony forgalom, furcsa keszleteltĂ©rĂ©s, hirtelen termek-visszaeses, szokatlan kosarertek.
8. Predikcio pesszimista/realista/optimista savval es konfidencia/bizonytalansagi intervallummal, nem egyetlen hamis pontossagu szammal.
9. Regression modellek: idojaras, het napja, event, trend es szezonalitas hatasa a bevetelre/keresletre.
10. Bayes-i frissites: keves adatnal ovatosabb, priorral tamogatott predikcio es fokozatos tanulas.
11. Scenario planning: mi van, ha esik az eso; mi van, ha telthazas event lesz; mi van, ha 20%-kal dragul az alapanyag.
12. Monte Carlo csak konkret dontesi helyzetben: elokeszitesi mennyiseg, keszlethiany kockazat, event profit range, heti cash-flow range.
13. ML modellek kesobbi, de fontos irany: demand forecasting, anomalia detektalas, basket recommendation es scenario/prediction engine; csak stabil historikus adat, mapping, dedupe es lineage utan.

### P2 - Weather es forecast

1. Weather cache marad adatbazis-alapu, nem requestenkenti provider hivas.
2. Forecast csak rovid tavon legyen konkret idojaras alapu.
3. 17-30 napra csak szezonalis/weather-normal becsles, explicit bizonytalansaggal.
4. ML csak stabil historikus adat, mapping es lineage utan.

## Kovetkezo konkret fejlesztesi sorrend

Ez a lista csak a nyitott, soron kovetkezo fejleszteseket tartalmazza. A mar lezart elemek az alatta levo merfoldko osszefoglaloba kerultek, hogy a sorvezeto tiszta maradjon.

1. PDF beszerzesi szamla kinyeres kovetkezo szelet: valodi PDF text/OCR adapter valasztas es beszallitoi szamla mintak validalasa, ha a konkret szamlak megerkeznek.
2. Recept/production workflow kovetkezo szelet: recept hiany/missing cost/missing vat tomeges muveletek es import/segedlet, ha a konkret receptlista megerkezik.
3. POS mapping/recept hiany munkalistak UX finomitasa: tomeges alias review, katalogusbol visszajelzes, mapping readiness allapotok.
4. Flow event elszamolasi melyites kovetkezo szelet: event koltsegsorok vagy ticket import adapter, performer settlement szabalyok es event profit osszehasonlitas.
5. Gourmand specifikus dashboard melyites: termek/recept/keszlet/weather osszefuggesek, elokeszitesi es keszlethiany dontestamogatas.
6. Inventory controlling ok- es item-szintu dontesi javaslatok melyitese a mar mentett kuszobok es periodus-osszehasonlitas alapjan.
7. Netto/brutto/AFA reporting kovetkezo melyitese: termek margin utan kategoriak/uzletagak osszesitett netto margin es AFA visszaigenylesi nezet.
8. Statisztikai alapok v1: adatminosegi kapuk, median/percentilisek, rolling trendek es elso anomalia modul valos dashboard kontextusban.
9. Predikcios alapok: pesszimista/realista/optimista savok, forecast readiness, majd regression/Bayes/scenario planning elokeszitese.
10. Technikai stabilitas: regresszios tesztcsomagok bovites, demo/test adat takaritas erosites, dokumentacio frissitese minden lezart szelet utan.

## Legutobb lezart merfoldkovek

A reszletes kesz allapot az `Allapot roviden` blokkban van. A fejlesztesi sorrendbol kivett, mar lezart fo iranyok:

- CSV-first iranyrogzites, POS idoszakmegjelenites, osszesito/teteles idoszak-ellenorzes es dedupe alap.
- POS termek/kategoria adaptacio, POS alias alap, mapping munkalista es recept hiany munkalista elso szeletei.
- POS import stabilitasi javitas: batch-en beluli POS alias deduplikacio, parse hiba utani rollback/failed statusz, es biztonsagos ures-batch helyreallito script.
- Recept ful es recept szerkeszto elso validacios UX.
- PDF beszerzesi szamla draft upload/list/review/konverzio alap, supplier item alias tanulassal es mapping munkalistaval.
- Magyar AFA torzsadat, product/inventory default AFA kapcsolat es Decimal alapu `VatCalculator`.
- Beszerzesi szamla posting elso cost update szelete: inventory item default cost frissites, source metadata es frissebb cost vedelem.
- Flow Business Dashboard scope es Event elemzo szetvalasztas, ticket actual elso integracio.
- Teoretikus keszlet, fizikai szamolas/korrekcio, variance okok, trend/top veszteseg, HUF becsles es elso anomalia statusz.
- Dashboard netto/brutto/AFA reporting foundation elso szelet: KPI amount basis/origin jeloles, kiadasi dashboard brutto actual + supplier invoice netto/AFA actual bontas, expense drill-down szamla netto/AFA/brutto osszesitessel.
- POS revenue derived AFA dashboard szelet: kategoria-, termek- es source-row bontasban a brutto actual mellett termek AFA torzsadatbol szamolt derived netto es AFA mezok jelennek meg, source jelolessel.
- POS AFA readiness/coverage szelet: a dashboard kulon jelzi az idoszaki POS brutto forgalom AFA-kulcs lefedettseget, a hianyos sorokat es a partial/complete/missing/no_data allapotot.
- Termek profit/margin reporting szelet: a termek endpoint es top termek UI brutto POS actual, derived netto/AFA, nettó COGS, nettó margin, margin % es `margin_status` mezoket ad.
- Recept/production AFA costing szelet: inventory item AFA kulcsbol soronkenti 5/18/27% derived AFA/brutto koltseg, recept total/unit brutto koltseg es `missing_vat_rate` jelzes.
- Inventory variance periodus-osszehasonlitas elso szelet: aktualis 30 nap vs elozo 30 nap HUF veszteseg, mennyiseg, esemenyszam, hianyzo ar jelzes, statusz es kezelesi javaslat a Becsult/Teoretikus keszlet oldalon.
- Inventory variance threshold konfiguracio: `inventory_variance_threshold` tabla, get/update API, uzletenkent mentheto magas veszteseg es romlas szazalek kuszob, frontend szerkesztes a Becsult/Teoretikus keszlet oldalon.
- Recept/production clean architecture elso szelet: a production modul mar nem placeholder; a `/api/v1/production/recipes` termekenkent ad recept, costing es readiness allapotot, a catalog read oldal pedig ezt a kozos modellt hasznalja.
- Production/Recept readiness frontend elso szelet: a Katalogus csoportbol elerheto munkanezet szuri es reszletezi a `missing_recipe`, `missing_cost`, `missing_stock`, `empty_recipe` es `ready` allapotokat.
- Recept save command refaktor: a catalog routerbol kikerult az aktiv receptverzio inaktivalasi/letrehozasi logika; production application command validal es repository ment.
- Onallo recipe write endpoint es frontend edit flow: a Recept readiness oldalrol mentheto az aktiv recept kovetkezo verzioja, a catalog product update nelkul.
- Recept readiness work queue elso szelet: a hiany kategoriak gyorsan kivalaszthatok, az osszetevo missing cost es becsult keszlet hiany a reszletpanelen azonnal javithato.
- Recept readiness missing VAT gyorsjavito szelet: kulon AFA hiany szuro, hivatalos AFA kulcs valaszto es inventory item `default_vat_rate_id` frissites a recept reszletbol.
- Recept sablonos inditas elso szelet: missing/empty recipe termeknel letezo recept betoltheto sablonkent a szerkesztobe, de mentest csak felhasznaloi ellenorzes utan indit.
- Recept verzio UX fegyelmezes: a szerkeszto jelzi az aktiv verziot es a kovetkezo mentessel letrejovo uj verziot, igy latszik, hogy a mentes publikalas jellegu uj aktiv verzio.
- Beszerzesi szamla read model AFA forrasjeloles: a procurement API es lista mar kulon adja, hogy a netto/AFA bontas teljes szamla-actual, reszleges vagy hianyzo.
- PDF szamla text-layer elotoltes elso szelet: uploadkor lefut a `text_layer_regex_v1` kinyero, `raw_extraction` audit adatot, confidence jelolest es review_payload elotoltest ad, de minden sor `review_needed` marad felhasznaloi ellenorzesig.
- DB tesztadat takaritas: `test-integration` business unit, hozza tartozo teszt kategoriak, inaktiv demo termekek es `Other Unit Supplier ...` teszt suppliers torolve; Gourmand/Flow real import alap megtartva.
- PDF extraction adapter boundary: a kinyero mar adapter contract mogott fut, igy kesobb OCR vagy beszallito-specifikus adapter illesztheto a review workflow megtorese nelkul.
- Recipe readiness overview API: `GET /api/v1/production/recipes/readiness-overview` uzletenkent ad missing recipe/cost/stock/VAT countereket es kovetkezo munkalista akciokat; a frontend summary ezt hasznalja.
- Flow event profit platform fee szelet: ticket actual platform fee bekerult az event performance elszamolasba, kulon `platform_fee_gross`, `operating_cost_gross`, `ticket_revenue_source` es `settlement_status` mezokkel.
- Flow event dontestamogato profit mutatok: az event performance mar ad `profit_status`, profit margin, koltsegarany, valamint jegy/bar beveteli mix szazalekokat; frontend event reszletben latszanak.
- Flow event osszehasonlito nezeti melyites: az event rangsor es summary mar profit status, margin, koltsegarany es jegy/bar mix alapjan is olvashato; a frontend nem szamol kulon uzleti igazsagot, az API read-model mezoket jeleniti meg.
- Flow event insight panel: az event analitika dontesi jelzeseket emel ki, peldaul legjobb uzleti eredmeny, magas koltsegarany, nepszeru de gyenge margin es barvezerelt event.
- Flow uzleti dashboard bekotes: a Business Dashboard Flow scope-ja mar betolti az event performance read-modelt, es az event dashboarddal azonos profit/margin/koltseg/mix alapokon mutatja a Flow uzleti event blokkot es forecast event elokeszitest.
- Gourmand dashboard placeholder takaritas: az uzleti fokusz `Idojaras kapcsolat` jelzese mar nem elokeszitett szoveg, hanem a weather-category insight read-model legerosebb tenyleges kapcsolatat mutatja.
- Frontend teljesitmeny elso szelet: route-level lazy loading bekerult, a nagy Dashboard/Event/Import/Procurement oldalak kulon chunkba kerulnek; a fo JS bundle a buildben kb. 224 kB-ra csokkent, a dashboard kulon kb. 78 kB chunk.
- Flow dashboard szerepszethuzas: a Flow uzleti dashboard event blokkja mar penzugyi event-hatas osszesito, nem eventenkenti rangsor/drilldown; a reszletes event osszehasonlitas az Event dashboard felelossege marad.
- Flow penzugyi mix szelet: a Flow specifikus dashboard blokk Gourmand mintara mar kategoriarangsorral mutatja a POS-alapu bar/fogyasztasi aranyt, atlagkosarat es csucsidot; jegyet nem keres POS-ban, a ticket actual kulon event penzugyi reteg.
- Flow POS-ticket korrekcio: az event performance es a Flow dashboard nem kovetkeztet jegyet POS termek/kategoria nevbol; minden POS sor bar/fogyasztasi bevetel, a jegy kizarolag ticket actual/import retegbol johet.
- Flow POS fogyasztasi kontrollkartya: a Flow uzleti dashboard mar kulon mutatja a POS-only bar/fogyasztasi koncentraciot, top 3 kategoriaranyt, csucsterhelest, kosarprofilt, kategoriamozgast es AFA readiness jelzest event rangsor nelkul.
- Event ticket actual lefedettseg szelet: az Event elemzo mar kulon jelzi a ticket actual coverage aranyt, a hianyzo ticket actual eventeket munkalistaban nyitja, es a szovegek ticket actual + POS bar alapon kezelik az event performance-t.

## Feature kesz definicio

Egy feature csak akkor tekintheto kesznek, ha:
- van domain jelentese es aktualis dokumentacioja
- backend use case es endpoint lefedi
- adatbazis/migration allapota tiszta
- integration teszt van a kritikus viselkedesre
- frontend flow hasznalja, ha user-facing feature
- dashboard vagy drill-down kapcsolat tiszta, ha elemzesi adatot termel
- actual/estimated/derived cimke nem keveredik
- hiba, hiany vagy nem teljes mapping nem okoz adatvesztest vagy alkalmazashibat

## Dontesi elvek

- CSV import az elso szamu sales truth source.
- Demo POS csak tesztkliens, nem termekirany.
- API ingestion csak boundary vagy jovobeli adapter, nem realtime dependency.
- A frontend megjelenit, a szamitas es validacio backend/domain oldalon tortenik.
- POS forgalmi importnal nincs kezi review: feltoltes utan dedupe vedett rogzitest inditunk.
- POS katalogus ar frissulhet automatikusan, de csak frissebb POS idopontbol; historical revenue mindig a teteles sor actual osszege.
- PDF szamla importnal kotelezo lesz a review es javitas a posting elott.
- A kod OOP, clean code, SOLID es modulhatar szerint bovul.
- A missing data allapot, nem kivetel: jelolni es kezelni kell, nem elrejteni vagy osszeomlani.
- Keszlethiany es recept hiany nem blokkolhat POS eladast, importot vagy dashboardot; ezek readiness jelzesek. Recept onkoltseg a legfrissebb ismert beszerzesi arbol szamolhato akkor is, ha a teoretikus keszlet nulla.
- A dashboard mindig forrasadatig visszakovetheto legyen.
- A penzugyi dashboardokon minden osszegrol latszodnia kell, hogy brutto actual, netto actual, AFA actual, vagy torzsadatbol szamolt derived adat. Ha a POS export nem ad AFA bontast, azt nem kezeljuk tenykent, csak egyertelmuen jelolt derived becsleskent.
- AFA-koros vallalkozasnal a recept/onkoltseg es margin alapja elsodlegesen netto koltseg, de brutto cash-flow es AFA osszeg is riportolando, mert a visszaigenyelheto AFA uzleti dontesben mas szerepet kap.
- A stock/inventory item AFA kulcsa domain adat: beszerzesi szamla review, receptkoltseg, termek profit es eladasi riport ugyanarra a torzsadatra epuljon, de minden szamitott adat legyen actual vagy derived jelolessel ellatva.
- Predikcio mindig bizonytalansagi savval es adatminosegi jelzessel jelenjen meg; az egyetlen pontosnak tuno elorejelzes felrevezeto.

