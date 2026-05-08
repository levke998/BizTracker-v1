# BizTracker Data Pipeline

Ez a dokumentum a ket importfolyam, a source lineage, a deduplikacio es a kesobbi accounting-ready adatkezeles igazsagforrasa.

## Ket Importfolyam

### 1. POS Forgalmi Import

A POS forgalmi import a kasszaprogram exportjabol dolgozik. Nem realtime API, hanem ket CSV-bol allo forgalmi csomag:
- `Osszesitett jelentes`: termeknev, kategoria, ar es osszesites.
- `Teteles jelentes`: datum, idopont, termeknev, ar, mennyiseg es brutto osszeg.

Workflow:

```text
osszesito CSV + teteles CSV
  -> feltoltes
  -> parse
  -> kategoria/termek adaptacio
  -> penzugyi rogzitest indit
  -> finance + dashboard + estimated consumption
```

POS importnal nincs kezi review dialog. Ha nincs technikai parse hiba, a felulet rogzitest indit. A posting dedupe vedett.

Fontos:
- a ket CSV ugyanarra az uzleti idoszakra vonatkozzon
- a teteles CSV adja a valos eladasi idopontokat
- az osszesito CSV adja a kategoriat
- fizetesi mod jelenleg nincs az exportban, ezert POS importbol nem varjuk
- a frontend import listaban latszik az importalt idoszak: elso es utolso teteles eladasi idopont
- a parser ellenorzi az `Adatok:` metadata idoszakot: az osszesito idoszakanak egyeznie kell a teteles fajlok egyuttes lefedesevel

### 2. PDF Beszerzesi Szamla Import

A szamla import kulon workflow lesz. Itt kotelezo az emberi ellenorzes.

Workflow:

```text
PDF feltoltes
  -> PDF draft tarolas
  -> adatkinyeres / OCR boundary
  -> szamla draft
  -> review dialog
  -> felhasznaloi javitas
  -> validalas
  -> finance + inventory posting
```

Review kotelezo, mert a szamlan beszallitoi, markaneves, kiszereleses termeknevek vannak, mikozben a receptben belso alapanyag fogalmak szerepelnek, peldaul `liszt`.

Netto/brutto/AFA pipeline:
- minden szamlasorhoz legyen AFA kulcs kapcsolat vagy review allapot
- product es inventory_item default AFA kulcsa a review es kalkulacio javaslati alapja
- `VatCalculator` a kozos Decimal alapu szamitasi mag: brutto/netto iranybol szamol, hianyzo AFA komponenst potol, elteresnel review jelzest ad
- ha a PDF-bol kinyert adat tartalmaz netto, AFA es brutto erteket, ezeket meg kell orizni es egymashoz validalni
- ha csak netto vagy brutto ertek olvashato ki, a `vat_rate` torzsadat alapjan szamoljuk a hianyzo mezoket
- ha a szamla es a szamolt ertek kozott kerekitesi tolerancian tuli elteres van, a sor review hibas lesz
- supplier item alias es inventory item mapping utan a jovobeli szamlakon az AFA kulcs javasolhato, de nem vakon auto-jovahagyott

Aktualis elso szelet:
- `core.supplier_invoice_draft` tarolja a PDF feltoltes review draft allapotat
- `POST /api/v1/procurement/purchase-invoice-drafts/pdf` PDF fajlt tarol es `review_required` draftot hoz letre
- `GET /api/v1/procurement/purchase-invoice-drafts` listazza a review draftokat
- `PUT /api/v1/procurement/purchase-invoice-drafts/{draft_id}/review` menti az ellenorzott fej- es soradatokat
- a review mentese soronkent a `VatCalculator` service-szel egyezteti a netto/AFA/brutto ertekeket
- hianyzo vagy ellentmondasos AFA adatnal a draft `review_required`, hibamentes soroknal `review_ready`
- `POST /api/v1/procurement/purchase-invoice-drafts/{draft_id}/create-purchase-invoice` csak `review_ready` draftbol hoz letre vegleges beszerzesi szamlat
- a konverzio utan a draft `invoice_created`, de finance/inventory posting meg nem tortenik
- `core.supplier_item_alias` tanulja a beszallitoi tetelnevet es a belso inventory item kapcsolatot
- ha a review sorban nincs inventory kapcsolat, az nem hiba: az alias `review_required`, es kesobb mapolhato
- ha a review sor inventory itemhez kapcsolodik, az alias `mapped`, es kovetkezo azonos beszallitoi tetelnevnel javaslatkent/automatikus kapcsolatkent hasznalhato
- `GET /api/v1/procurement/supplier-item-aliases` listazza a beszallitoi alias munkalistat
- `PATCH /api/v1/procurement/supplier-item-aliases/{alias_id}/mapping` manualisan inventory itemhez kapcsol egy alias sort
- a Procurement / Szamlak oldalon van PDF review panel
- a Procurement / Szamlak oldalon ismeretlen tetelbol letrehozhato uj belso keszletelem/aru torzselem
- a Procurement / Szamlak oldalon van beszallitoi alias munkalista manualis jovahagyassal
- OCR/adatkinyeres meg nem tortenik, a felhasznalo manualisan rogzithet/javithat review sorokat

## POS CSV Parser

Aktualis import profilok:
- `gourmand_pos_sales`
- `flow_pos_sales`
- `pos_sales` legacy/generic tesztprofil

Parser felelosseg:
- fajl olvasas
- kodolas es separator kezeles
- metadata/header sorok kezelese
- magyar penzformatum olvasasa
- kedvezmeny szoveg megorzese
- teteles sorok normalizalasa
- osszesito alapjan kategoria hozzarendeles
- source line key kepzes, ha nincs kulso ID
- parse hibak import row/error szinten

Domain mapping felelosseg:
- business unit
- product/category adaptacio
- POS/SKU/barcode alias nyilvantartas
- aktualis katalogus ar frissitese POS megfigyelesbol
- finance transaction letrehozas
- estimated consumption audit inditasa
- dashboard read-modelhez source lineage

## POS Product Alias Es Mapping

Aktualis alap:
- `core.pos_product_alias` tarolja a POS exportbol erkezo termekazonossagot
- source key prioritas: POS product id, SKU, barcode, majd normalizalt termeknev
- uj POS termeknev automatikusan bekerul `auto_created` statuszba
- egy import batch-en belul ugyanaz a POS source key csak egy alias rekordot hozhat letre; az ismetlodo sorok az `occurrence_count`, `first_seen_at` es `last_seen_at` mezoket frissitik
- `mapping_confidence` jelzi, hogy nev, SKU vagy barcode alapu volt-e az automatikus kapcsolat
- `occurrence_count`, `first_seen_at`, `last_seen_at` es `last_import_batch_id` segiti a review munkalistat
- `GET /api/v1/pos-ingestion/product-aliases` listazza a mapping/quarantine sorokat
- `PATCH /api/v1/pos-ingestion/product-aliases/{alias_id}/mapping` manualisan termekhez koti az aliast es `mapped` statuszba allitja
- az Import kozpontban van elso POS mapping munkalista termekvalasztassal
- kovetkezo importnal a `mapped` alias iranyitja a catalog sync es estimated consumption termekfeloldast

## Flow Ticket Actual

Kulon ticket rendszer kezeli a jegyertekesitest, ezert a jegyadat nem POS CSV import resze.

Workflow:

```text
event letrehozas -> ticket actual rogzites/import -> Event elemzo performance
```

Aktualis elso szelet:
- `core.event_ticket_actual` tarolja az eventhez kapcsolt jegy actualt
- `GET /api/v1/events/{event_id}/ticket-actual` visszaadja a rogzitett jegyadatot
- `PUT /api/v1/events/{event_id}/ticket-actual` letrehozza vagy frissiti a jegy actualt
- az Events feluleten a kinyitott eventnel van `Jegyadatok` panel
- az event performance jegybevetel es jegydarabszam mezoi a ticket actualbol dolgoznak, ha van ilyen adat

Fontos:
- event letrehozaskor a jegyadat nem kotelezo
- POS CSV tovabbra is bar/fogyasztas actual
- ticket actual lehet kezi rogzites, kesobb ticket CSV/API adapter
- AFA kulcs opcionalisan kapcsolhato a ticket actualhoz

## POS Recept Hiany Munkalista

Uj POS termek eseten a rendszer automatikusan letrehozza a termeket, de receptet nem talal ki.
Ez nem import hiba, hanem nem blokkoló munkalista allapot.

Aktualis alap:
- `GET /api/v1/pos-ingestion/products/missing-recipes` listazza a POS-bol erkezo aktiv termekeket, amelyekhez nincs aktiv recept
- a lista POS aliasbol indul, tehat csak kasszabol latott termekeket jelez
- szerepel benne a termek, kategoria, aktualis ar, POS forras, elofordulas es utolso latott idopont
- az Import kozpontban kulon `POS recept munkalista` panel mutatja a hianyokat
- a dashboardon ez nem jelenik meg kulon figyelmezteteskent
- POS importot nem blokkol, de jelzi, hogy a recept/COGS/inventory becsles nem teljes

## Production Recept Readiness

A recept es onkoltseg olvasasi oldala a production modulba kerult, hogy a catalog, inventory es kesobbi dashboard ugyanarra a szabalyra epuljon.

Aktualis alap:
- `GET /api/v1/production/recipes` termekenkent ad aktiv recept, aktiv receptverzio, osszetevo, costing es readiness allapotot
- a valasz tartalmazza: `cost_status`, `readiness_status`, `warnings`, `known_total_cost`, `total_cost`, `unit_cost`
- nincs recept eseten `no_recipe` / `missing_recipe` allapot jon vissza, nem hiba
- ures recept eseten `empty_recipe` allapot jon vissza, nem import vagy eladas blokker
- hianyzo beszerzesi/default koltseg eseten `missing_cost`; ilyenkor `unit_cost` nincs, nehogy reszleges koltseg hamis teljes onkoltsegnek tunjon
- nulla vagy hianyzo teoretikus keszlet eseten `missing_stock` readiness jelzes johet, de az onkoltseg tovabbra is szamolhato az aktualis default beszerzesi arbol
- a Catalog termeklista recept/onkoltseg read oldala mar ezt a production read modellt hasznalja
- a frontend Recept readiness oldala ugyanezt a read modellt mutatja, kulon szurokkel a missing recipe, missing cost, missing stock, empty recipe es ready allapotokra
- a catalog product create/update recept mentese mar production application commandon keresztul tortenik, ezert a receptverzio mentese nem a catalog router felelossege
- `PUT /api/v1/production/products/{product_id}/recipe` onalloan menti a termek kovetkezo aktiv receptverziojat, majd friss production readiness sort ad vissza
- a frontend Recept readiness oldala ezt az endpointot hasznalja receptnev, kihozatal, mertekegyseg es osszetevo sorok mentesehez
- a frontend Recept readiness munkalista gyors gombokkal szur missing recipe, missing cost, missing stock es empty recipe allapotra
- missing cost gyorsjavitas a kapcsolt inventory item `default_unit_cost` mezojet frissiti a catalog ingredient API-n keresztul
- missing/unknown/insufficient stock gyorsjavitas a kapcsolt inventory item `estimated_stock_quantity` mezojet frissiti; ez tovabbra is teoretikus/controlling adat, nem fizikai leltar

## POS Aradaptacio

POS CSV arszabaly:
- a teteles POS sor brutto osszege historical actual, ezt semmilyen kesobbi katalogus arvaltozas nem irhatja felul
- a `product.sale_price_gross` csak aktualis katalogus ar, nem historikus revenue alap
- POS import kozben az uj termek es kategoria automatikusan letrejon, ha meg nincs
- POS import kozben a termek aktualis katalogus ara automatikusan frissul, ha frissebb POS sorbol latjuk
- `sale_price_last_seen_at` tarolja, hogy a katalogus ar melyik POS idopontbol ismert
- `sale_price_source` jelzi az ar forrasat, peldaul `pos_sales` vagy `gourmand_pos_sales`
- regebbi idoszak utolagos feltoltese nem irhatja vissza az aktualis arat regebbi ertekre

Pelda:
- 2026-05-01: termek 100 Ft
- 2026-05-02: termek 150 Ft
- ha a 2026-05-02 import elobb erkezik, majd kesobb a 2026-05-01 import, a katalogus aktualis ara marad 150 Ft
- a 2026-05-01 penzugyi tranzakcio tovabbra is 100 Ft actual marad

Kovetkezo lepes:
- tomeges jovahagyas es keresheto mapping review UX
- bizonytalan vagy hianyzo mapping ne inditson eros inventory/recept kovetkeztetest
- dashboard jelezze, ha egy KPI vagy drill-down nem teljesen jovahagyott mappingre epul

## POS Deduplikacio

Nincs stabil kulso ID a teteles es osszesitett exportban, ezert a rendszernek logikai dedupe kulcsot kell kepeznie.

Dedupe key elemek:
- business unit
- occurred_at vagy date/time
- product/source product name
- quantity
- gross amount
- source line key, ha elerheto

Szabaly:
- ugyanaz a CSV ujrafeltoltve ne hozzon letre uj penzugyi tranzakciot
- ha ugyanarra a napra delben es este is jon export, a del elotti sorok ne duplazodjanak, az uj delutani/esti sorok rogzuljenek
- estimated consumption csak nem duplikalt sorra fusson
- dashboard csak dedupe utan rogzitett adatbol szamoljon

Technikai vedelmek:
- a parse kozbeni catalog sync hiba utan a session rollback kotelezo, majd a batch `failed` statuszt kapjon, ne ragadjon `parsing` allapotban
- a POS alias sync nem szurhat be ket azonos `(business_unit_id, source_system, source_product_key)` rekordot ugyanabban a batch-ben
- a finance mapping adatbazisban mar letezo dedupe kulcsokat es az aktualis batch-en beluli ismert dedupe kulcsokat is kihagyja
- beragadt, de meg ures batch helyreallitasara az operacios script: `python -m scripts.recover_import_batch --batch-id <uuid> --apply --map-finance`

## POS Idoszak

A feltoltott forgalmi csomag idoszaka a teteles sorokbol szamolodik:
- `first_occurred_at`
- `last_occurred_at`

Ez az import lista resze. Nem kotjuk meg, hogy napi, heti vagy napon beluli export legyen.

Aktualis erosites:
- az osszesito CSV `Adatok:` metadata idoszaka es a teteles CSV-k metadata idoszaka explicit ossze van vetve
- elteres eseten `pos_period_mismatch` parse hiba keletkezik, sorok nem rogzulnek
- tobb teteles fajl eseten a teteles fajlok egyuttes minimum/maximum idoszaka szamit

## PDF Szamla Adatok

Szamla draft mezok:
- supplier
- invoice number
- invoice date
- due date
- currency
- raw supplier item name
- matched inventory item
- quantity
- unit
- net unit price
- gross unit price
- VAT rate
- net line total
- VAT amount
- gross line total

Mapping:
- beszallitoi termeknev -> belso inventory item
- markanev es kiszereles nem zavarhatja meg a recept alapu alapanyag fogalmat
- bizonytalan mapping `review` vagy `quarantine` allapotba kerul
- jovahagyott mapping kesobb ujrahasznalhato alias legyen
- a szamlan szereplo raw nev es a belso megjelenitesi/tarolt nev kulon kezelendo
- ha a tetel nem letezik meg, a reviewbol uj inventory item felveheto; termek/recept kapcsolat kesobb epulhet ra

## AFA, Netto Es Brutto

Accounting-ready irany:
- AFA kulcsokat rogzitunk
- beszerzesi szamlaknal netto, AFA es brutto szinten is tarolunk
- dashboard kiadas oldalon brutto es netto nezet is kell
- AFA osszeg riportolhato legyen
- POS oldalon, ha az export nem ad AFA bontast, nem talalunk ki tenyadatot; kesobb termek/AFA szabalybol derived netto/AFA szamitas keszulhet
- elso dashboard reporting szelet kesz: KPI-k jelolik az osszeg alapjat (`gross`, `net`, `mixed`) es eredetet (`actual`, `derived`)
- supplier invoice eredetu kiadasnal a dashboard a szamlasorokbol netto es AFA actual bontast ad, mas kiadasi forrasnal `not_available` bontast jelez
- POS bevetel jelenleg `gross actual`; POS netto/AFA csak kesobbi, product/vat master data alapu `derived` pipeline lehet

## API Felulet Rovid

POS import:
- `POST /api/v1/imports/files`
- `POST /api/v1/imports/file-set`
- `GET /api/v1/imports/batches`
- `POST /api/v1/imports/batches/{batch_id}/parse`
- `GET /api/v1/imports/batches/{batch_id}/rows`
- `GET /api/v1/imports/batches/{batch_id}/errors`
- `POST /api/v1/imports/batches/{batch_id}/map/financial-transactions`
- `GET /api/v1/pos-ingestion/product-aliases`
- `GET /api/v1/pos-ingestion/products/missing-recipes`
- `PATCH /api/v1/pos-ingestion/product-aliases/{alias_id}/mapping`

Production/recept:
- `GET /api/v1/production/recipes`
- `PUT /api/v1/production/products/{product_id}/recipe`

Szamla/procurement jelenlegi alap:
- `POST /api/v1/procurement/purchase-invoice-drafts/pdf`
- `GET /api/v1/procurement/purchase-invoice-drafts`
- `PUT /api/v1/procurement/purchase-invoice-drafts/{draft_id}/review`
- `POST /api/v1/procurement/purchase-invoice-drafts/{draft_id}/create-purchase-invoice`
- `GET /api/v1/procurement/supplier-item-aliases`
- `PATCH /api/v1/procurement/supplier-item-aliases/{alias_id}/mapping`
- `POST /api/v1/procurement/purchase-invoices`
- `POST /api/v1/procurement/purchase-invoices/{purchase_invoice_id}/post`
- postingkor a kapcsolt inventory item `default_unit_cost` mezje frissul a szamlasor netto egysegarabol
- a cost update forrasolt: `supplier_invoice_line` source type, szamlasor source id es invoice date alapu last-seen ido
- regebbi szamla nem irja felul a frissebb beszerzesi/default costot
- a posting valaszban latszik, hany inventory item cost frissult (`updated_inventory_item_costs`)
- a Procurement szamlalistaban latszik, ha egy szamlan van inventory mapping nelkuli sor; ilyen sorbol nem lesz cost frissites
- a Catalog / Alapanyagok nezetben latszik a beszerzesi koltseg hianya, forrasa es utolso frissitesi ideje
- ha a Catalogban kezzel modositjuk a default koltseget, a cost source `manual` lesz; torolt koltsegnel a source metadata is torlodik
- a cost source nem FIFO es nem keszletretegezesi alap; a teljes teoretikus keszlet aktualis erteke mindig a legfrissebb ismert beszerzesi arbol szamolodik
- a szamlasor lineage technikai audit es bizalmi jelzes, nem fo felhasznaloi drill-down cel

Kesobbi PDF szamla import endpointok: OCR/adatkinyeres inditasa es supplier item alias/mapping tanulas.

Inventory korrekcio:
- `POST /api/v1/inventory/physical-stock-counts` fizikai szamolasbol keszletkorrekciot rogzit
- payload: business unit, inventory item, megszamolt mennyiseg, mertekegyseg, ok-kod es opcionalis megjegyzes
- a backend az aktualis stock levelhez kepest szamolja az elterest, majd `adjustment` vagy `waste` inventory movementet hoz letre
- a movement `source_type` erteke `physical_stock_count`, a `reason_code` pedig a felhasznaloi ok-kategoria
- ok-kategoriak: `physical_count`, `waste`, `breakage`, `spoilage`, `theft_suspected`, `recipe_error`, `mapping_error`, `missing_purchase_invoice`, `other`
- `GET /api/v1/inventory/variance-reasons` ok-kod szerint osszesiti a korrekcios movementeket
- az osszesites mezoi: ok-kod, esemenyszam, osszes erintett mennyiseg, netto keszlethatas es utolso elofordulas
- `GET /api/v1/inventory/variance-trend` napi idosort ad az utolso N nap hiany/veszteseg, tobblet es netto keszlethatas adataibol
- `GET /api/v1/inventory/variance-items` keszletelem szerint rangsorolja a hiany/veszteseg es tobblet korrekciokat
- a trend es item endpoint HUF becslest ad az aktualis default beszerzesi ar alapjan: becsult hiany/veszteseg, becsult tobblet es becsult netto hatas
- hianyzo default cost eseten a rendszer nem talal ki penzerteket; `missing_cost_movement_count` es `missing_cost` anomalia statusz jelzi a hianyt
- elso anomalia statuszok: `normal`, `watch`, `repeating_loss`, `high_loss`, `missing_cost`, `surplus_review`
- `GET /api/v1/inventory/variance-period-comparison` az aktualis idoszakot az elozo azonos hosszu idoszakkal hasonlitja ossze
- `inventory_variance_threshold` uzletenkent menti a `high_loss_value_threshold` es `worsening_percent_threshold` kuszobokat
- a periodus-osszehasonlitas alapbol a mentett uzleti kuszobot hasznalja, request szintu kuszob csak explicit felulirasra marad
- periodus dontesi statuszok: `stable`, `improving`, `watch`, `worsening`, `critical`, `missing_cost`; a valasz mindig tartalmaz kezelesi javaslatot
- a frontend Becsult/Teoretikus keszlet oldala ezt Eltérés okok panelkent mutatja
- ugyanott az Eltérés trend es veszteseg panel az utolso 30 napot es a legnagyobb vesztesegu keszletelemeket mutatja

## Teoretikus Keszlet Es Eltérés

A Gourmand keszlet nem fizikai, real-time raktarprogramkent mukodik, hanem controlling becsleskent:
- a bejovo beszerzes noveli az actual/teoretikus alapot
- a POS eladas recept alapjan becsult alapanyag-fogyast general
- selejt, tores, kiborulas, dolgozoi fogyasztas vagy lopas csak akkor latszik, ha fizikai szamolas/korrekcio vagy szokatlan variance jelzi
- a rendszernek nem kell tudnia, melyik konkret szamlasorbol szarmazik a felhasznalt liszt

Keszlet ertek szabaly:
- nincs FIFO retegzes az MVP-ben
- minden inventory item aktualis `default_unit_cost` erteke a legfrissebb ismert beszerzesi ar
- a teljes teoretikus mennyiseg erteke: `theoretical_quantity * current_default_unit_cost`
- korabbi beszerzesi arak nem torzulnak el finance actualban, de a jelenlegi keszlet ertek becsles mindig friss arbol szamol
- elso API szelet kesz: `/api/v1/inventory/theoretical-stock` visszaadja a `default_unit_cost`, `actual_stock_value`, `theoretical_stock_value`, `variance_stock_value` es `variance_status` mezoket
- elso frontend szelet kesz: a Becsult/Teoretikus keszlet oldalon osszesitett teoretikus keszlet ertek, hiany gyanu es hianyzo ar indikator latszik
- masodik szelet kesz: ugyanebben a nezetben kivalasztott sorhoz fizikai szamolas, ok-kategoria es megjegyzes rogzitese indithato

Eltérés jelzes cel:
- ha a rendszer szerint van keszlet, de a valosagban nincs, az inventory korrekcio vagy fizikai szamolas utan variance-kent jelenjen meg
- negativ vagy szokatlan variance lehet selejt, pazarlas, lopas, hibas recept, hibas mapping vagy kimaradt beszerzesi szamla jele
- ez fontosabb felhasznaloi irany, mint a konkret cost source szamlasorra visszanyitasa

Variance statuszok:
- `ok`: van teoretikus keszlet es ar, nincs mennyisegi eltérés
- `missing_theoretical_stock`: nincs teoretikus keszletadat, ez recept/fogyasi szabaly vagy kezdeti keszlet hianyra utalhat
- `missing_cost`: van teoretikus mennyiseg, de nincs aktualis beszerzesi ar
- `shortage_risk`: actual mennyiseg kisebb, mint a teoretikus, ez hiany/selejt/pazarlas/lopas gyanu
- `surplus_or_unreviewed`: actual mennyiseg nagyobb, mint a teoretikus, ez kimaradt fogyas, hibas recept, kimaradt mapping vagy extra korrekcio jele lehet

## Adatbiztonsagi Szabalyok

- raw file/source record ne vesszen el
- normalized payload legyen visszakeresheto
- POS posting idempotens legyen
- PDF szamlanal validalas elott ne legyen vegleges finance/inventory posting
- dedupe es source reference kotelezo
- hiba es missing mapping legyen felhasznaloi allapot, ne rejtett log
