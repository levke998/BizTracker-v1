# BizTracker Domain Model

Ez a dokumentum a termek- es domain dontesek egyseges helye. A BizTracker ket konkret uzletre epul: `Gourmand` es `Flow Music Club`.

## Alapfilozofia

A rendszer controlling es dontestamogato alkalmazas, nem hivatalos konyvelesi motor.

Adatretegek:
- `actual`: tenylegesen rogzitett eladas, szamla, beszerzes, keszletmozgas
- `estimated`: receptbol, fogyasi szabalybol vagy forecastbol szamitott becsles
- `derived`: actual es estimated adatokbol kepzett dashboard/read-model

Kulcsszabaly:

```text
actual != estimated
```

Ezt UI-ban, API-ban, adatmodellben es dokumentacioban is jelolni kell.

## Gourmand modell

Fo kerdesek:
- mely kategoriak es termekek hozzak a bevetelt
- mennyi a becsult onkoltseg es arres
- milyen alapanyag es recept kockazat van
- hogyan hat az idojaras es idoszak a keresletre
- milyen elokeszitesi vagy keszletdontes javasolt

Fontos objektumok:
- `product`: amit eladunk
- `inventory_item`: amit beszerzunk, tarolunk, felhasznalunk
- `recipe`: product es inventory_item kozti BOM kapcsolat
- `recipe_version`: torteneti es koltsegezesi pontossag miatt
- `recipe_ingredient`: mennyiseg, mertekegyseg, koltseg alap
- `estimated_consumption`: sales alapu becsult alapanyag-fogyas

Recept irany:
- a Termekkatalogus alatt legyen kulon `Receptek` ful; elso UX szelet kesz
- egy termekhez lehet aktiv receptverzio
- recept nelkul is letezhet termek, de margin/stock jelzese korlatozott
- recept hiany nem okozhat hibat, csak kockazati allapotot
- hianyzo alapanyag vagy keszletadat nem blokkolhat eladast/importot
- nulla vagy hianyzo teoretikus keszlet mellett is szamolhato a recept onkoltseg, ha az osszetevok aktualis beszerzesi/default koltsege ismert
- ha valamelyik osszetevo beszerzesi/default koltsege hianyzik, a rendszer nem becsul alul csendben: `missing_cost` costing allapotot ad, es csak a reszleges ismert koltseget jelzi
- aktualis backend read-side: `GET /api/v1/production/recipes` termekenkent ad `cost_status`, `readiness_status`, `warnings` es osszetevo stock/cost jelzest
- aktualis frontend read-side: a Recept readiness munkanezet uzletenkent listazza es szuri a `missing_recipe`, `missing_cost`, `missing_stock`, `empty_recipe` es `ready` allapotokat
- POS-bol automatikusan letrejott termek recept nelkul `missing recipe` munkalista elem
- recept mentese elott UI szinten is jelezni kell az ures, hianyos vagy duplikalt alapanyag sorokat
- recept mentese backend oldalon production application use case-en keresztul tortenik: `SaveActiveProductRecipeCommand` validalja az ures receptet, duplikalt osszetevot, mertekegyseget es business unit hatart
- a catalog product create/update meghivja ezt a production commandot, de mar van onallo production write endpoint is: `PUT /api/v1/production/products/{product_id}/recipe`
- a Recept readiness frontend munkanezetbol mentheto a recept neve, kihozatala, mertekegysege es osszetevo listaja; a mentes uj aktiv receptverziot hoz letre
- a Recept readiness munkanezet nem gyart automatikusan receptet; a missing recipe, missing cost es missing stock kategoriak munkalista jelzesek
- missing cost es missing/unknown/insufficient stock gyorsjavitasnal a felhasznalo az erintett inventory item aktualis default arat vagy becsult keszletmennyiseget potolja, ezutan a readiness read-model ujraszamolodik

Gourmand consumption logika:

```text
CSV sales actual -> product mapping -> active recipe -> estimated ingredient usage -> estimated COGS -> dashboard
```

POS product alias:
- a POS exportbol erkezo source termeknev/SKU/barcode kulon mapping rekord
- az automatikusan letrehozott termek nem azonos a felhasznalo altal jovahagyott mappinggel
- `auto_created` allapot review munkalista alap, nem vegleges uzleti igazolas
- `mapped` felhasznaloi jovahagyast jelent, es kovetkezo importnal a POS source nev ezt a belso termeket hasznalja
- recept es inventory fogyas csak biztos termekkapcsolatnal lehet eros uzleti jelzes

POS ar es historikus tenyadat:
- a POS CSV sor brutto osszege revenue actual
- a katalogus aktualis eladasi ara csak torzsadat, amely a legfrissebb POS megfigyeleshez igazodik
- `sale_price_last_seen_at` nelkul nem dontheto el, hogy egy ar frissebb-e, ezert ezt a termeken taroljuk
- regi import nem irhatja vissza a mai katalogus arat
- arvaltozas nem rontja el a multbeli dashboard szamitasokat, mert azok import row/finance actual osszegbol dolgoznak
- recept hiany uj POS termeknel kockazati allapot, nem import blokker

## Flow modell

Fo kerdesek:
- mennyi a jegybevetel, bar revenue es Flow-nal marado resz
- milyen idoszakban es idojarasnal eros a barfogyasztas
- mely eventek teljesitenek jol, es melyik volt a legfelkapottabb

Fontos objektumok:
- `event`: idosav, statusz, performer, varhato letszam
- `event_ticket_actual`: kulon ticket rendszerbol erkezo jegy darabszam, brutto/netto/AFA es platform dij actual
- `ticket revenue`: `event_ticket_actual`, kesobb ticket CSV/API importbol; a Flow POS CSV nem tartalmaz jegyet es nincs POS-alapu jegybecsles
- `bar revenue`: POS/CSV sales actual
- `performer share`: konfiguralt szazalek vagy kesobb szabaly
- `fixed fee`: fix fellepti dij
- `event cost`: eventhez kapcsolt koltseg
- `event performance`: idosav alapu read-model

Event late-binding:
- eladas event nelkul is tenyadat
- ha event kesobb jon letre ugyanarra az idosavra, a read-model utolag hozzakapcsolja a POS sorokat
- nem kell placeholder eventet letrehozni minden eladashoz

Flow UI scope:
- a Business Dashboard `flow` scope-ja az uzleti/beveteli oldalt mutatja, Gourmandhoz hasonlo vezetoi nezettel
- a Flow dashboard KPI, trend, kategoria, termek, bar/fogyasztasi mix es csucsidovezetett forgalmi kerdesekre valaszol
- a Flow penzugyi mix POS-alapu: bar/fogyasztasi forgalom; a ticket actual az event penzugyi retegben marad
- a Flow POS kontrollkartyaja bar/fogyasztasi mutatokat mutat: vezeto kategoria, top 3 koncentracio, csucsterheles, kosarprofil, kategoriatrend es AFA readiness
- a Flow dashboard event blokkja ugyanarra az event performance read-modelre epul, mint az Event/Esemeny elemzo, de penzugyi osszesito szerepu: event hatas a Flow eredmenyre, ticket actual lefedettseg, event koltsegarany es jegy/bar mix
- az Event/Esemeny elemzo fule az eventek osszehasonlitasa: legerosebb, legfelkapottabb, performer, jegy/bar mix, POS sor/nyugta es weather kontextus
- az Event/Esemeny elemzo reszletes eventenkenti rangsor/drilldown, a Flow dashboard nem masolja ezt a feladatot
- az Event/Esemeny elemzo ticket actual lefedettseget es hianyzo ticket actual munkalistat is mutat, mert a jegybevetel nem POS-bol becsult adat
- event rangsor vagy event munkalista nem kerul a dashboardra kulon blokkent
- kesz elso szelet: letrehozott eventhez manualisan rogzithet ticket actual, amely az Event elemzo performance ticket reteget adja; hianyaban a ticket bevetel nincs rogzitve

Egyszerusitett Flow profit:

```text
retained_ticket_revenue + POS bar_revenue - performer_fixed_fee - event_cost - ticket_platform_fee
```

Az alap 80% performer share lehet uzleti kiindulas, de nem kodba egetett szabaly.

Event performance elszamolasi jeloles:
- `ticket_revenue_source`: `ticket_actual` vagy `not_recorded`
- `settlement_status`: `actual_ticket_settlement` vagy `ticket_actual_missing`
- `operating_cost_gross`: fix fellepti dij + egyeb event koltseg + ticket platform fee
- `profit_status`: `profitable`, `break_even`, `loss` vagy `no_revenue`
- `event_profit_margin_percent`: event profit / sajat bevetel
- `operating_cost_ratio_percent`: event mukodesi koltseg / sajat bevetel
- `ticket_revenue_share_percent`, `bar_revenue_share_percent`: teljes brutto event beveteli mix

## Inventory

Inventory szerepe:
- beszerzes es keszlethelyzet kovetese
- keszleten allo penz becslese
- estimated COGS es margin alapja
- theoretical stock es variance alap
- kesobbi FIFO-compatible metadata csak technikai lehetoseg, de a Gourmand controlling MVP nem FIFO szemleletu

Actual inventory:
- purchase
- initial_stock
- adjustment
- waste
- manual correction

Estimated inventory:
- recept alapu fogyas
- eladas alapu theoretical stock
- forecast alapu elokeszitesi jelzes

Theoretical stock cel:

```text
theoretical_quantity = actual incoming/corrections - estimated consumption
variance = actual_quantity - theoretical_quantity
```

Gourmand keszlet szemlelet:
- a keszlet teoretikus, mert a rendszer nem tudja pontosan, mennyi liszt borul ki, mennyi tojas torik el, vagy mennyi alapanyag fogy el nem recept szerinti okbol
- ugyanazon inventory item keszletet nem bontjuk beszerzesi retegekre
- ha 5 kg liszt korabban 5000 Ft/kg aron erkezett, majd 20 kg 6000 Ft/kg aron, akkor a teljes teoretikus 25 kg aktualis beszerzesi ara 6000 Ft/kg
- a keszleten allo penz controlling becsles, nem hivatalos FIFO/LIFO valuation
- a teoretikus mennyiseg fogyasa recept alapu POS eladasbol jon, nem fizikai meresbol

MVP-ben a teljes theoretical engine nincs kesz. Van actual stock level, estimated stock quantity es estimated consumption audit. Ezeket nem szabad teljes fizikai raktarkeszletkent kommunikalni. Az elso uzleti theoretical stock szelet mar mutatja az actual mennyiseget, teoretikus mennyiseget, aktualis beszerzesi ar alapu keszlet erteket es variance statuszt.

Fizikai szamolas/korrekcio elso szelet:
- a `POST /api/v1/inventory/physical-stock-counts` endpoint egy adott inventory item megszamolt mennyiseget rogzit
- a backend kiszamolja az elozo aktualis keszlethez kepest az elterest, es inventory movementet hoz letre
- pozitiv vagy nulla kulonbseg `adjustment`, negativ kulonbseg `waste` jellegu korrekcios movement
- a movement `reason_code` mezoben tarolja az okot: `physical_count`, `waste`, `breakage`, `spoilage`, `theft_suspected`, `recipe_error`, `mapping_error`, `missing_purchase_invoice`, `other`
- a frontend Becsult/Teoretikus keszlet oldalon a kivalasztott sorhoz rogzithet fizikai szamolast, okot es megjegyzest
- a `GET /api/v1/inventory/variance-reasons` endpoint ok-kod szerint osszesiti a korrekcios movementeket, es mutatja az esemenyszamot, osszes mennyiseget, netto keszlethatast es utolso elofordulast
- a `GET /api/v1/inventory/variance-trend` endpoint napi bontasban mutatja a korrekcios esemenyeket, hiany/veszteseg mennyiseget, tobbletet es netto keszlethatast
- a `GET /api/v1/inventory/variance-items` endpoint keszletelem szerint rangsorolja a korrekciokat, kulon hiany/veszteseg es tobblet mennyiseggel
- a trend es item read-model HUF becslest is ad az aktualis `inventory_item.default_unit_cost` alapjan; ez controlling becsles, nem hivatalos konyvelesi valuation
- az item read-model elso anomalia statuszokat ad: `missing_cost`, `watch`, `repeating_loss`, `high_loss`, `surplus_review`, `normal`
- a Becsult/Teoretikus keszlet oldalon megjelent az Eltérés okok panel, amely nem dashboard KPI, hanem inventory controlling munkafelület
- ugyanitt megjelent az Eltérés trend es veszteseg panel, amely az utolso 30 napot es a legnagyobb vesztesegu tetelek listajat mutatja
- a `GET /api/v1/inventory/variance-period-comparison` endpoint az aktualis idoszakot az elozo azonos hosszu idoszakkal veti ossze; HUF veszteseg, mennyiseg, esemenyszam, hianyzo ar, valtozas szazalek es dontesi statusz jelenik meg
- elso periodus dontesi statuszok: `stable`, `improving`, `watch`, `worsening`, `critical`, `missing_cost`
- `inventory_variance_threshold` uzletenkent tarolja a magas veszteseg HUF kuszobot es a romlas szazalekos kuszobot
- a periodus-osszehasonlitas a mentett business-unit kuszobokat hasznalja, explicit request parameter csak feluliras/spike celra marad
- a Becsult/Teoretikus keszlet oldalon a kuszobok szerkeszthetok, igy a controlling jelzes nem kodba egetett szabaly
- ez controlling jelzes: segit kiszurni selejtet, pazarlast, lopasgyanut, hibas receptet, hibas mappinget vagy kimaradt beszerzesi szamlat, de nem hivatalos leltarkonyv

## Procurement es accounting-ready irany

Beszerzesi szamla kritikus workflow:

```text
PDF feltoltes -> PDF draft -> adatkinyeres -> review dialog -> felhasznaloi javitas -> validalas -> posting -> finance + inventory
```

Aktualis alap:
- PDF feltoltes es `review_required` draft tarolas kesz
- a draft meg nem vegleges szamla es nem indit finance/inventory postingot
- `review_payload` mar menti az ellenorzott fej- es soradatokat
- PDF review menteskor soronkent lefut a netto/AFA/brutto egyeztetes a `VatCalculator` service-szel
- ha minden review sor kalkulacioja `ok`, a draft `review_ready`; ha hiany vagy elteres van, marad `review_required`
- `review_ready` draftbol letrehozhato a vegleges `supplier_invoice`; ilyenkor a draft `invoice_created`
- a vegleges szamla letrehozasa meg nem posting: finance es inventory actual csak kulon konyvelesi muvelet utan keletkezik
- `raw_extraction` mar tarolja az elso `text_layer_regex_v1` kinyero audit payloadjat es confidence jeloleset; ez csak elotoltes, nem actual adat
- az elotoltott PDF sorok `review_needed` allapotban maradnak, hogy a felhasznalo ellenorizze a beszallitoi nevet, belso megjelenitesi nevet, mennyiseget, AFA kulcsot es netto/brutto ertekeket

Szamlaadatok:
- supplier
- invoice number
- invoice date
- due date
- currency
- line name raw supplier termeknevvel
- matched inventory item
- quantity
- unit
- net unit price
- gross unit price
- VAT rate
- net line total
- VAT amount
- gross line total

Fontos problema:
- a szamlan nem "liszt" vagy "tojas" szerepel, hanem markanev, kiszereles es beszallitoi termeknev
- emiatt kell supplier item alias/mapping
- a rendszer tanuljon mappinget jovahagyas utan
- nem biztos mapping eseten quarantine/review allapot kell
- a szamlan szereplo raw tetelnev megorzendo, de a belso tarolt/megjelenitesi nev review kozben javithato
- ha nincs egyezes a belso torzsben, ez nem hiba: a sor maradhat mapping nelkul, vagy a review dialogbol uj inventory item/aru torzselem hozhato letre
- `supplier_item_alias` kulon kezeli a beszallitoi tetelnevet, a belso display nevet es az inventory item kapcsolatot
- a Procurement / Szamlak alias munkalistaja listazza a review_required es mapped beszallitoi tetelneveket
- manualis jovahagyaskor az alias inventory itemhez kapcsolodik, `mapped` statuszt kap, es kesobbi review soroknal feloldasi javaslatkent hasznalhato
- TopJoy-szeru beszallitoi aruk es klasszikus alapanyagok ugyanabban a review flow-ban kezelhetok; recept kapcsolat csak akkor kell, ha eladott termek fogyasat akarjuk belole szamolni

Posting hatas:
- financial outflow actual
- inventory purchase movement actual
- cost basis frissites kontrollaltan
- source lineage a szamlara es szamlasorra

## Costing

Aktualis costing:
- direkt termek: `product.default_unit_cost`
- receptes termek: aktiv receptverzio osszetevoi es `inventory_item.default_unit_cost`
- g/kg es ml/l alap atvaltas tamogatott
- estimated COGS nem FIFO es nem hivatalos COGS
- receptes termeknel a keszlethiany nem nullazza es nem blokkolja az onkoltseget; a cost alapja az aktualis default beszerzesi ar, a stock pedig kulon readiness jelzes
- a production recipe read modell allapotai: `complete`, `missing_cost`, `no_recipe`, `empty_recipe`; readiness oldalon `ready`, `missing_recipe`, `missing_cost`, `missing_stock`, `empty_recipe`
- a Catalog termeklista recept/onkoltseg olvasasa mar ezt a production read modellt hasznalja, igy a recept costing szabaly egy helyre kerult
- procurement postingkor a vegleges beszerzesi szamlasor netto egysegarabol frissul az `inventory_item.default_unit_cost`
- az inventory item tarolja a cost forrast: `default_unit_cost_last_seen_at`, `default_unit_cost_source_type`, `default_unit_cost_source_id`
- regebbi szamla kesobbi postingja nem irhatja felul a frissebb default costot
- Catalog kezi koltsegmodositasnal a source `manual`, source id nelkul; uresre allitott koltsegnel a source metadata is ures
- a Catalog alapanyag kartyaja uzleti allapotkent jelzi, ha nincs beszerzesi koltseg, nincs forras, vagy szamlasorbol frissult az adat
- a cost source nem fo felhasznaloi drill-down cel; elsodleges szerepe az, hogy latszodjon, friss szamlabol vagy kezi beallitasbol jon-e az aktualis beszerzesi ar

Kovetkezo costing irany:
- netto/brutto/AFA tarolas
- AFA kulcsok rogzitheto, riportolhato kezelese
- aktualis beszerzesi ar es teoretikus keszlet ertek kovetkezetes szetvalasztasa
- keszlet variance jelzes selejt, pazarlas, lopas vagy recept/mapping hiba gyanura
- keszleten allo penz controlling becsles

AFA torzsadat:
- legyen kulon `vat_rate` torzsadat tabla hivatalos magyar kulcsokkal es ervenyessegi idoszakkal
- kezdeti magyar kulcsok: 27%, 18%, 5%, 0%, valamint kulon kezelendo specialis adozasi kodok (peldaul adomentes/forditott adozas), ha szamlabol ilyen erkezik
- a tabla ne csak szazalekot, hanem kodot, megnevezest, tipus/kategoria mezot, `valid_from`, `valid_to`, `is_active` allapotot es NAV/riport mapping mezot is tartalmazzon
- brutto -> netto: `net = gross / (1 + rate)`
- netto -> brutto: `gross = net * (1 + rate)`
- AFA osszeg: `vat = gross - net`
- szamitas Decimal alapon, soronkénti kerekitesi szaballyal tortenjen; float nem hasznalhato penzugyi szamitasra
- elso kalkulator service kesz: `VatCalculator` brutto/netto iranybol szamol, hianyzo komponenseket potol, es tolerancian tuli elteresnel `review_needed` statuszt ad

AFA hozzarendeles:
- product es inventory_item kapjon default `vat_rate_id` mezot; elso backend/frontend szelet kesz `default_vat_rate_id` mezovel
- purchase invoice line tarolja a szamlan szereplo AFA kulcsot es a szamitott/ellenorzott netto, AFA, brutto erteket
- PDF draft review sorok es vegleges supplier invoice line sorok is ugyanezt az ellenorzott netto/AFA/brutto strukturat hasznaljak
- ha a szamla ad netto/brutto/AFA adatot, azt actual forrasnak tekintjuk es csak ellenorizzuk a torzsadat szerinti szamitassal
- ha a szamlan hianyzik valamelyik komponens, akkor a rogzitett AFA kulcsbol szamoljuk ki
- ha eltérés van a szamla es a szamolt ertek kozott, review allapotban kell jelezni, nem automatikusan felulirni
- AFA kulcs termeknevbol vagy beszallitoi nevre illesztve csak javaslat lehet; vegleges kulcs torzsadat/mapping vagy user review utan legyen

Recipe/costing AFA irany:
- recept onkoltseg controllinghoz elsodlegesen netto beszerzesi koltsegbol szamoljon, mert AFA-koros vallalkozasnal a levonhato input AFA nem termekköltség
- brutto beszerzesi ertek is latszodjon, mert cash-flow es kifizetesi oldalon fontos
- a recept osszetevoi kulon-kulon hordozzak az inventory item AFA kulcsat; egy recepten belul lehet 5%, 18% es 27% is
- a recept read model soronkent szamol derived AFA-t es bruttot a netto default beszerzesi arbol, majd osszegzi total/unit szinten
- ha egy osszetevonek van netto koltsege, de nincs AFA kulcsa, a netto onkoltseg tovabbra is hasznalhato, de `missing_vat_rate` figyelmeztetes es tax statusz jelenik meg
- Flow eseteben is ugyanaz az inventory/product AFA modell ervenyes, csak ott jellemzoen tovabbertekesitett termekek es egyszeru mixek vannak, nem osszetett gyartasi receptek
- ha az uzlet AFA profilja kesobb mas (peldaul alanyi adomentes), a cost basis szabaly konfiguraciobol valtoztathato legyen

Dashboard accounting irany:
- bevetel es kiadas brutto erteken jelenleg is ertelmezheto
- kovetkezo accounting-ready iranyban minden szamla es beszerzes tarolja a netto, AFA es brutto erteket
- ahol a POS export nem ad fizetesi modot vagy AFA bontast, azt nem talaljuk ki
- termek/AFA torzsadatbol derived netto/AFA szamitas keszulhet, de ez nem kassza-actual adat
- dashboard mutatoknal vilagosan jelezni kell, hogy brutto actual, netto derived vagy AFA derived adatrol van szo
- elso reporting szelet kesz: dashboard KPI-k `amount_basis` es `amount_origin` mezot kapnak, a POS bevetel `gross` + `actual`, a becsult COGS `net` + `derived`, a vegyes margin pedig `mixed` + `derived`
- POS kategoriabontas, termekbontas es termek source-row drill-down elso derived AFA szelete kesz: `revenue/gross_amount` tovabbra is brutto actual, `net_revenue/net_amount` es `vat_amount` pedig `product_vat_derived`
- POS AFA readiness jelzes kesz: a `DashboardVatReadiness` az idoszak brutto POS forgalmat, AFA-kulccsal lefedett es hianyos reszet, sor darabszamokat, coverage szazalekot es statuszt tartalmaz
- Termek margin read model elso szelet kesz: a termek sorok tartalmazzak a derived netto bevetelt, derived AFA-t, netto COGS-t, netto margin osszeget/szazalekot, `cost_source` es `margin_status` jelolest
- kiadasi dashboardon a financial transaction osszeg tovabbra is brutto actual penzmozgaskent szerepel
- ha a kiadas forrasa supplier invoice, a read-model a szamlasorokbol netto es AFA actual bontast is ad; mas forrasnal a tax breakdown `not_available`, nem becsult
- supplier invoice drill-downban a szamla brutto, netto es AFA osszesitese jelenik meg, a sorok tovabbra is a review/posting soradatokra epulnek
- procurement supplier invoice list/get read modelben is van `tax_breakdown_source`, hogy a felulet ne keverje ossze a teljes, reszleges es hianyzo AFA bontast

## Dashboard domain

Dashboard scope-ok:
- `overall`: osszesitett uzleti kep
- `gourmand`: Gourmand termek/recept/keszlet/weather fokusz
- `flow`: Flow uzleti/beveteli fokusz, jegy/bar mixszel es forgalmi ritmussal
- Gourmand weather fokusz: az uzleti fokusz panel weather-category insightbol mutatja a legerosebb kategoriat es idojarasi kapcsolatot, nem statikus placeholdert

Drill-down cel:

```text
KPI -> chart -> category/product/event context -> source row / invoice / receipt
```

Dashboardon mindig latszodjon:
- mi actual
- mi estimated
- mi forecast
- mihez hianyzik mapping vagy adat

## Statisztikai es prediktiv elemzes

Cel:
- a rendszer ne csak leirja, mi tortent, hanem dontest tamogasson
- a predikcio mindig savos legyen: pesszimista, realista, optimista
- a statisztikai mutato csak akkor keruljon UI-ra, ha van hozza uzleti kerdes vagy kovetkezo cselekves

Leiro statisztika:
- atlag melle median kell ott, ahol szelso ertekek torzithatnak: kosarertek, napi bevetel, event bevetel, termek darabszam
- percentilisek/kvantilisek kotelezoen tervezett mutatok: P25, P75, P90, P95; ezek jobban mutatjak az eloszlas also/felso savjait, mint az atlag
- szoras ott hasznos, ahol a kiszamithatatlansag maga a kockazat: napi/oras forgalom, termekkereslet, event teljesitmeny, keszlet variance
- hisztogram/eloszlas akkor hasznos, ha a forma dontest ad: kosarertek savok, csucsidok, napi forgalmi eloszlas, termek demand savok
- rolling average es mozgo median kell idosorokra, mert a napi adat zajos; kezdeti ablakok: 7 es 14 nap
- szezonalitas bontas: het napja, napszak, honap, unnepnap, event-nap es idojaras

Kovetkeztetesi statisztika:
- korrelacio/kovariancia hasznalhato idojaras-termek, idojaras-kategoria, event-bar fogyasztas es egyutt vasarolt termekek elemzesere
- korrelacio nem okozatisag; UI-ban mintaszam, idoszak es adatminoseg jelzes kell
- szezonalitast, het napjat, napszakot es event-hatast kulon kell kezelni, kulonben hamis idojaras-kapcsolatot mutathat
- kosar-asszociaciohoz korrelacio helyett/ mellett association rule mining kell: support, confidence, lift
- anomalia detektalas tervezett: szokatlan forgalom, termek-visszaeses, keszleteltérés, kosarertek kiugras, import vagy mapping gyanus hatas

Predikcio:
- rovid tavu forecast: kovetkezo napok/orak kereslete, elokeszitesi javaslat, keszlethiany kockazat
- kozep tavu becsles: heti cash-flow, alapanyag beszerzesi igeny, event varhato profit
- minden predikcio legyen actual/estimated/forecast cimkezve, confidence/adatminoseg jelzessel
- pesszimista/realista/optimista savok fontosabbak, mint egyetlen pontosnak tuno szam
- konfidencia intervallum vagy bizonytalansagi sav kotelezo prediktiv UI elem
- regression modellek tervezett szerepe: idojaras, het napja, event, trend es szezonalitas hatasa a bevetelre vagy termekkeresletre
- Bayes-i frissites tervezett szerepe: keves adatnal ovatosabb predikcio, amely prior feltetelezest hasznal es uj adatokkal fokozatosan frissul
- scenario planning tervezett: eso, telthazas event, alapanyag dragulas, varatlan hiany vagy magas kereslet hatasa

Monte Carlo:
- csak akkor erdemes, ha van bizonytalansagi eloszlas es konkret dontes
- jo helye: event profit range, heti cash-flow range, keszlethiany valoszinuseg, elokeszitesi mennyiseg kockazata
- nem jo helye: alap KPI kartyak, kis mintaszamu termekek, frissen bevezetett mapping nelkuli adatok

ML modellek:
- fontos jovobeli irany, mert a predikcio es dontestamogatas a rendszer egyik fo erteke
- kezdeti modellek legyenek ertelmezheto baseline-ok, majd cserelhetok erosebb ML modellekre
- tervezett ML teruletek: demand forecasting, anomalia detektalas, kosarajanlas/basket recommendation, event teljesitmeny becsles, keszlethiany kockazat, scenario/prediction engine
- ML nem indulhat stabil historikus adat, dedupe, mapping, source lineage es adatminosegi scoring nelkul

Adatminosegi kapuk:
- nincs predikcio elegendo historikus adat, dedupe, mapping es source lineage nelkul
- kis mintanal csak "figyelendo jelzes" lehet, eros kovetkeztetes nem
- outlier es import hiba kulon jelolendo, mert a median/eloszlas ellenallobb, de a predikcio torzulhat

## Hianykezeles

Hiany vagy bizonytalansag nem lehet crash ok.

Kotelezo allapotok:
- missing mapping
- low confidence mapping
- auto-created POS alias
- missing recipe
- missing cost
- missing stock
- missing VAT data
- unreviewed invoice extraction
- duplicate/import skipped

Ezeket UI-ban is uzleti allapotkent kell megmutatni.

Aktualis UI alap:
- Import kozpont: POS alias mapping munkalista
- Import kozpont: POS recept munkalista kasszabol ismert, de recept nelkuli termekekre
- Dashboard: nem jelenit meg kulon POS recept hiany munkalistat
