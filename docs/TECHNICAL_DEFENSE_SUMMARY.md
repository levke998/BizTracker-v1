# BizTracker szakmai osszefoglalo

## 1. Az alkalmazas celja

A BizTracker egy belso uzleti elemzo es controlling rendszer, amely ket konkret uzleti egyseg, a Gourmand es a Flow Music Club mukodeset koveti. A rendszer nem konyvelesi program es nem realtime kasszarendszer, hanem forrasadatig visszakovetheto dontestamogato alkalmazas. Fo celja, hogy a kasszaexportokbol, beszerzesi szamlakbol, receptekbol, keszletmozgasokbol, event adatokbol es idojarasi adatokbol olyan dashboardokat es munkalistakat keszitsen, amelyek segitik a napi uzleti donteseket.

A fejlesztes alapelve a CSV-first adatfeldolgozas. Ez azt jelenti, hogy a POS/kasszaadatokat nem kozvetlen kassza API-n keresztul vesszuk at, hanem ellenorizheto CSV exportokbol. Az adat utja:

```text
raw fajl -> import_file -> import_batch -> import_row -> domain mapping -> finance / inventory / analytics read model
```

A rendszer kulon kezeli a tenyleges adatot, a becslest es a szarmaztatott mutatokat:

- `actual`: rogzitett tenyadat, peldaul POS brutto bevetel, beszerzesi szamla, inventory movement.
- `estimated`: receptbol vagy szabalybol szamitott becsles, peldaul alapanyag-fogyas es teoretikus keszlet.
- `derived`: actual es estimated adatokbol kepzett dashboard mutato, peldaul estimated COGS, margin vagy kockazati statusz.

Ez az elvalasztas a teljes rendszer egyik legfontosabb szakmai dontese: az alkalmazas nem allitja be tenyadatnak azt, amit csak becsulni tud.

## 2. Technologiai felepites

A BizTracker modularis monolitkent epul. A backend FastAPI, SQLAlchemy 2 es Alembic alapu Python alkalmazas, a frontend React, TypeScript, Vite es TanStack Query alapu kliens. A celarchitektura PostgreSQL adatbazisra epul.

A backend moduljai:

- `identity`: bejelentkezes, token, aktualis user.
- `master_data`: uzleti egysegek, lokaciok, mertekegysegek, kategoriak, termekek, AFA kulcsok.
- `imports`: fajlfeltoltes, batch, parse, import row, parse hiba.
- `pos_ingestion`: POS termekalias, mapping, recepthiany munkalista, becsult fogyas inditasa.
- `finance`: penzugyi tranzakciok, POS sorokbol beveteli actualok.
- `catalog`: termekek es alapanyagok kezelesi felulete.
- `production`: recept, receptverzio, osszetevok, costing es readiness.
- `inventory`: keszletelem, keszletmozgas, actual stock, estimated consumption audit, theoretical stock, variance.
- `procurement`: beszallitok, beszerzesi szamlak, PDF draft/review, posting.
- `events`: Flow event planner, ticket actual, event performance.
- `weather`: idojaras observation es forecast cache.
- `analytics`: dashboard, drill-down, trendek, weather/forecast read model.

A frontend modulonkenti szerkezetet hasznal:

```text
src/modules/<module>/
  pages/
  api/
  hooks/
  types/
  components/
```

A frontend feladata a megjelenites, interakcio, validacios UX es query cache. A komolyabb uzleti szamitasok backend oldalon, application/domain vagy read-model retegben tortennek.

## 3. Fo kesz funkciok

Jelenleg kesz es mukodo alapok:

- FastAPI backend es React/TypeScript frontend.
- Auth MVP: login, `/me`, token, vedett route-ok.
- CSV import upload, batch, parse, sorok es hibak kezelese.
- Gourmand es Flow POS CSV profilok.
- POS osszesito es teteles fajlok idoszak-ellenorzese.
- POS sorok penzugyi tranzakciova alakitasa deduplikacioval.
- POS product alias es manual mapping munkalista.
- POS-bol ismert, de recept nelkuli termekek munkalistaja.
- Termek- es alapanyagkatalogus.
- Recept/BOM modell, aktiv receptverzio, production recipe read API.
- Recept readiness frontend: `missing_recipe`, `missing_cost`, `missing_stock`, `empty_recipe`, `ready`.
- Recept mentese onallo production endpointon keresztul.
- Estimated COGS es margin szamitas recept vagy direkt koltseg alapjan.
- Inventory item, inventory movement, actual stock level.
- POS eladasokbol becsult alapanyag-fogyas es audit sor.
- Teoretikus keszlet, keszletertek, variance statusz.
- Fizikai keszletszamolasbol korrekcios movement.
- Variance okok, trend, item rangsor, HUF becsles, periodus-osszehasonlitas.
- Beszerzesi szamla, PDF draft upload/list/review, netto/AFA/brutto ellenorzes.
- Supplier item alias tanulas es mapping.
- Beszerzesi szamla posting finance es inventory actual iranyba.
- Dashboard valos adatbol: KPI, trend, kategoria, termek, kosar, kiadas, stock/product risk.
- Weather cache es forecast cache alapu dashboard insightok.
- Flow event CRUD, ticket actual es event performance alap.

## 4. Konkret szamitasok es uzleti logika

### 4.1 POS import es deduplikacio

A POS import sorai eloszor normalizalt import sorok lesznek. A penzugyi rogzitest csak `parsed` allapotu batchre engedi a rendszer. Egy POS sorbol `pos_sale` tipusu, `inflow` iranyu HUF penzugyi tranzakcio keszul.

A tranzakcio osszege:

```text
amount = normalized_payload.gross_amount
```

Az idopont:

```text
occurred_at = normalized_payload.occurred_at
```

ha nincs ilyen, akkor a `date` mezobol nap eleji UTC idopont keszul.

A dedupe kulcs SHA-256 hash, amely normalizalt komponensekbol epul:

```text
business_unit_id
date
receipt_no
product_name
quantity 0.001 pontossagra kerekitve
gross_amount 0.01 pontossagra kerekitve
source_line_key, ha van
```

Ez vedi ki, hogy ugyanaz a CSV ujrafeltoltve duplazza a bevetelt. A mapping parancs az adatbazisban mar letezo dedupe kulcsokat es az aktualis batchen beluli ismert kulcsokat is ellenorzi.

### 4.2 POS termekmapping

A POS exportban erkezo termeknev, SKU vagy barcode nem azonos automatikusan a belso termektorzzsel. A rendszer kulon `pos_product_alias` rekordot tart fenn. A source product key prioritas:

```text
source_product_id -> sku -> barcode -> normalizalt product_name
```

Az automatikusan letrejott kapcsolat `auto_created` allapotban review munkalista elem. Csak a `mapped` statuszu alias jelent felhasznaloi jovahagyast. Ez fontos adatminosegi kapu: a dashboard es az estimated consumption erosebb kovetkeztetesei csak biztosabb termekkapcsolat mellett megbizhatoak.

### 4.3 Recept es onkoltseg

A recept logika a production modulban van. Egy termekhez aktiv recept es aktiv receptverzio tartozhat. A recept osszetevoi inventory itemekre mutatnak. A recept onkoltsege:

```text
ingredient_converted_quantity = ingredient.quantity mertekegyseg-konverzioval
ingredient_cost = ingredient_converted_quantity * inventory_item.default_unit_cost
known_total_cost = osszes ismert ingredient_cost osszege
total_cost = known_total_cost, ha nincs hianyzo koltseg; kulonben None
unit_cost = total_cost / recipe_version.yield_quantity
```

Tamogatott alap konverziok:

```text
g <-> kg
ml <-> l
```

Ha egy osszetevo koltsege hianyzik, a rendszer nem mutat hamis teljes onkoltseget. Ilyenkor:

```text
cost_status = missing_cost
unit_cost = None
known_total_cost = csak az ismert reszkoltsegek osszege
```

Readiness statuszok:

- `missing_recipe`: nincs aktiv recept.
- `empty_recipe`: van recept, de nincs osszetevo.
- `missing_cost`: van recept, de hianyzik osszetevo koltseg.
- `missing_stock`: a koltseg szamolhato, de keszletadat hianyzik vagy nem elegendo.
- `ready`: van recept, koltseg es nincs stock warning.

Ez a megoldas Clean Code szempontbol azert fontos, mert a costing/readiness szabaly egy production read modelben van, nem szetszorva frontend komponensekben vagy catalog router helper fuggvenyekben.

### 4.4 Estimated consumption es teoretikus keszlet

POS eladas utan a rendszer megprobalja feloldani a termeket. A sorrend:

```text
product_id -> mapped POS alias -> SKU -> product_name
```

Ha van aktiv recept, akkor recept alapu fogyas keszul:

```text
estimated_ingredient_usage =
  recipe_ingredient.quantity * sold_quantity / recipe_yield_quantity
```

Ezutan a mennyiseg atvaltodik az inventory item mertekegysegebe. A becsult keszlet csokken:

```text
quantity_after = max(0, quantity_before - converted_quantity)
```

Minden ilyen muvelet `estimated_consumption_audit` sort hoz letre, amely tarolja:

```text
product_id
inventory_item_id
recipe_version_id
source_type
source_id
source_dedupe_key
receipt_no
estimation_basis = recipe vagy direct_product
quantity
quantity_before
quantity_after
occurred_at
```

Ha nincs recept, a rendszer direkt termek-keszlet kapcsolatot keres: azonos nevu, aktiv, track_stock inventory itemet. Ha ez sincs, nincs csendes hamis fogyas.

### 4.5 Actual stock es theoretical stock

Az actual stock inventory movementekbol epul:

```text
current_quantity =
  purchase + initial_stock + adjustment - waste
```

A teoretikus mennyiseg jelenleg az inventory item `estimated_stock_quantity` mezojebol jon, amelyet POS fogyas csokkenthet. A theoretical stock read model:

```text
theoretical_quantity = estimated_stock_quantity
variance_quantity = actual_quantity - theoretical_quantity
actual_stock_value = actual_quantity * default_unit_cost
theoretical_stock_value = theoretical_quantity * default_unit_cost
variance_stock_value = variance_quantity * default_unit_cost
```

Ha barmelyik mennyiseg vagy koltseg hianyzik, a penzertek `None`, nem kitalalt becsles.

Variance statuszok:

- `missing_theoretical_stock`: nincs teoretikus adat.
- `missing_cost`: van teoretikus mennyiseg, de nincs beszerzesi ar.
- `ok`: nincs elteres.
- `shortage_risk`: actual kisebb, mint theoretical.
- `surplus_or_unreviewed`: actual nagyobb, mint theoretical.

Ez controlling logika, nem hivatalos FIFO/LIFO keszletertekeles. A teljes teoretikus keszlet erteke mindig az aktualis `default_unit_cost` alapjan szamolodik.

### 4.6 Fizikai keszletszamolas es variance

A fizikai szamolas endpoint egy megszamolt mennyiseget kap. A rendszer lekeri az aktualis stock szintet, majd kiszamolja:

```text
adjustment_quantity = counted_quantity - current_quantity
```

Ha az elteres pozitiv vagy nulla:

```text
movement_type = adjustment
quantity = adjustment_quantity
```

Ha negativ:

```text
movement_type = waste
quantity = abs(adjustment_quantity)
```

A `reason_code` uzleti okot tarol, peldaul `physical_count`, `waste`, `breakage`, `spoilage`, `theft_suspected`, `recipe_error`, `mapping_error`, `missing_purchase_invoice`, `other`.

A variance trend HUF becslese:

```text
estimated_shortage_value = waste_quantity * default_unit_cost
estimated_surplus_value = adjustment_quantity * default_unit_cost
estimated_net_value_delta = surplus_value - shortage_value
```

Periodus-osszehasonlitasnal az aktualis idoszak az elozo azonos hosszu idoszakhoz merodik:

```text
shortage_value_change = current_shortage_value - previous_shortage_value
change_percent = (current - previous) / previous * 100
```

A dontesi statusz uzletenkent mentett kuszobokbol jon:

- `missing_cost`: van veszteseg, de hianyzik cost.
- `critical`: aktualis veszteseg meghaladja a high loss HUF kuszobot.
- `worsening`: a veszteseg romlasa meghaladja a romlasi szazalekos kuszobot.
- `improving`: csokken a veszteseg.
- `watch`: van figyelendo korrekcios aktivitas.
- `stable`: nincs erdemi jelzes.

### 4.7 AFA, netto es brutto

Penzugyi szamitasnal a rendszer `Decimal` tipust hasznal, nem lebegopontos `float`-ot. Az AFA kalkulacio:

```text
factor = 1 + rate_percent / 100
net = gross / factor
gross = net * factor
vat = gross - net
```

A penzertekek ket tizedesre, `ROUND_HALF_UP` modon kerekitodnek.

A `VatCalculator` harom fo modot tud:

- `calculate_from_gross`: bruttobol nettot es AFA-t szamol.
- `calculate_from_net`: nettobol bruttot es AFA-t szamol.
- `reconcile`: a szamlan megadott netto/AFA/brutto adatokat egyezteti.

Ha a szamla es a szamolt ertek a tolerancian tul elter, a statusz:

```text
review_needed
```

es a hibalista peldaul `net_amount_mismatch`, `vat_amount_mismatch`, `gross_amount_mismatch` lehet.

### 4.8 Beszerzesi szamla es posting

A PDF beszerzesi szamla eloszor draft:

```text
PDF upload -> supplier_invoice_draft -> review_required
```

A review sorok manualisan ellenorizhetok. A `VatCalculator` soronkent validalja a netto/AFA/brutto adatokat. Hibamentes review utan a draft `review_ready`, majd vegleges `supplier_invoice` hozhato letre. A vegleges szamla letrehozasa meg nem posting.

Postingkor ket actual hatas keletkezik:

```text
finance outflow:
  amount = invoice.gross_total
  source_type = supplier_invoice

inventory purchase movement:
  movement_type = purchase
  quantity = invoice_line.quantity
  unit_cost = invoice_line.line_net_amount / invoice_line.quantity
  source_type = supplier_invoice_line
```

Emellett a kapcsolt inventory item aktualis beszerzesi/default koltsege frissul:

```text
default_unit_cost = line_net_amount / quantity
default_unit_cost_source_type = supplier_invoice_line
default_unit_cost_source_id = invoice_line.id
default_unit_cost_last_seen_at = invoice_date
```

Vedoszabaly: regebbi szamla nem irhatja felul a frissebb costot, ha az item `default_unit_cost_last_seen_at` erteke kesobbi, mint a most postolt szamla datuma.

### 4.9 Dashboard KPI-k

A dashboard backend read modelbol keszul. A fo KPI-k:

```text
revenue = sum(financial_transaction.amount where direction = inflow)
cost = sum(financial_transaction.amount where direction = outflow)
profit = revenue - cost
estimated_cogs = sum(product_unit_cost * sold_quantity)
margin_profit = revenue - estimated_cogs
gross_margin_percent = margin_profit / revenue * 100
```

A termek unit cost:

```text
ha van aktiv recept:
  recipe_unit_cost = recipe_total_cost / yield_quantity
kulonben:
  product.default_unit_cost
```

A POS bontasok import row payloadbol keszulnek:

```text
category_revenue = sum(gross_amount csoportositva category_name szerint)
product_revenue = sum(gross_amount csoportositva product_name szerint)
quantity = sum(quantity)
transaction_count = sorok szama
```

POS netto/AFA read model:

```text
gross_amount = POS actual
net_amount, vat_amount = product.default_vat_rate_id alapjan derived
vat_readiness = AFA-kulccsal lefedett brutto forgalom / osszes POS brutto forgalom
estimated_cogs_net = product_unit_cost * sold_quantity
estimated_net_margin = net_amount - estimated_cogs_net
margin_status = complete | partial | missing_vat_rate | missing_cost | missing_vat_and_cost
```

Kosarmutatok:

```text
basket_key = receipt_no, ha van; kulonben import_row.id
average_basket_value = sum(basket gross_amount) / basket_count
average_basket_quantity = sum(basket quantity) / basket_count
```

A dashboard KPI-k `amount_basis` es `amount_origin` mezokkel jelolik, hogy az adott osszeg brutto/netto/mixed es actual/derived eredetu-e.

### 4.10 Idojaras es forecast insight

Az idojaras nem requestenkent kulso API-bol jon, hanem cache-elt adatbazis read modelbol. A forecast hatas a kovetkezo 7 napra keszul. A rendszer a forecast napokat homerseklet- es allapot-savokba rendezi, majd historikus POS napokhoz hasonlitja.

Prioritas a baseline valasztasnal:

```text
1. azonos temperature_band + condition_band historikus atlag
2. azonos het napja szerinti atlag
3. teljes historikus atlag
```

Ennek megfeleloen a confidence:

```text
magas -> pontos weather condition egyezes
kozepes -> weekday baseline
alacsony -> overall average
```

Ez nem ML modell, hanem ertelmezheto baseline alapu elso forecast/readiness szelet.

### 4.11 Flow event profit

A Flow event domainben a jegy- es barbeveteleket kulon kezeli a rendszer. A jegyadat manualisan rogzitett vagy kesobbi ticket adapterbol erkezo `event_ticket_actual`; a Flow POS CSV nem tartalmaz jegyet, ezert nincs POS-alapu jegybecsles az event performance read modelben.

Egyszerusitett Flow profit:

```text
performer_share_amount = ticket_revenue_gross * performer_share_percent / 100
retained_ticket_revenue = ticket_revenue_gross - performer_share_amount
own_revenue = retained_ticket_revenue + bar_revenue_gross
event_profit_lite = own_revenue - performer_fixed_fee - event_cost_amount
```

Ez settlement-lite modell: dontestamogato event teljesitmenyt ad, de meg nem teljes elszamolasi motor.

## 5. Clean Code es SOLID megvalositas

A rendszerben a modularis monolit nem egyszeru mappastruktura, hanem tudatos felelossegelvalasztas.

### Single Responsibility

Az egyes osztalyok es service-ek egy jol korulhatarolt feladatot kapnak:

- `VatCalculator`: csak netto/AFA/brutto szamitas es egyeztetes.
- `MapPosSalesBatchToTransactionsCommand`: parsed POS batch penzugyi tranzakciova alakitasa.
- `PosSaleInventoryConsumptionService`: POS sorbol estimated consumption es estimated stock csokkentes.
- `SqlAlchemyRecipeRepository`: recipe costing/readiness read model.
- `PostPurchaseInvoiceCommand`: posting use case inditasa es duplazas elleni vedelem.

### Open/Closed Principle

A dashboard es a forecast logika ugy epul, hogy uj read-model mezok es uj insightok hozzaadhatok anelkul, hogy a meglovo import vagy finance alaplogikat at kellene irni. A POS import profilok (`gourmand_pos_sales`, `flow_pos_sales`) is bovitheto iranyt adnak.

### Liskov es Interface Segregation

A domain/application retegek repository contractokon keresztul dolgoznak. A use case nem a teljes adatbazis implementaciot ismeri, hanem csak a szukseges muveleteket. Ez kulonosen latszik a production recipe es inventory query/command szeletekben.

### Dependency Inversion

A magas szintu application use case-ek nem kozvetlenul SQLAlchemy query-kbol indulnak, hanem repository interfeszekre es service-ekre epulnek. Az ORM az infrastructure retegben marad. Ez csokkenti a csatolast, es tesztelhetove teszi az uzleti logikat.

### Clean Code gyakorlatok

- A hianyos adat nem kivetel, hanem allapot: `missing_cost`, `missing_recipe`, `review_needed`, `missing_theoretical_stock`.
- Penzugyi szamitasok `Decimal` alapon futnak.
- Magic number helyett konfiguralt vagy adatbazisban tarolt kuszobok vannak, peldaul inventory variance threshold.
- A dashboard nem frontend oldalon szamol, hanem backend read modelbol kap jelolt adatokat.
- A source lineage megmarad: import row, source id, dedupe key, supplier invoice line source.
- A modulhatarok explicitek: catalog nem kozvetlenul kezeli a receptverzio mentest, hanem production commandot hiv.
- Az idempotencia kritikus helyeken megjelenik: POS dedupe, beszerzesi szamla posting duplazas elleni ellenorzes.

## 6. Adattudomanyi es elemzesi szemlelet

A rendszer jelenlegi adattudomanyi erteke a stabil, visszakeresheto adatpipeline es az ertelmezheto read model. A modell nem feketedobozos ML-lel indul, hanem:

- historikus POS sorokbol aggregalt KPI-ket keszit,
- nyugtaszintre csoportositott kosarmutatokat szamol,
- recept es alapanyagkoltseg alapjan estimated COGS-t ad,
- actual es estimated keszlet kozotti variance-t jelez,
- idojaras/forecast baseline alapjan keresleti insightokat keszit,
- event profitot komponensekre bontva szamol.

A fontos adattudomanyi vedelmek:

- actual, estimated es derived adatok elkulonitese,
- mapping confidence es review allapotok,
- deduplikacio,
- source lineage,
- hianyzo cost vagy mapping eseten nem tortenik hamis ertekpotlas,
- forecastnal confidence jelzes van.

## 7. Jelenlegi korlatok

A rendszer mar eros MVP, de nem teljes vegtermek. Fontos korlatok:

- A POS import stabil, de a tomeges alias review UX meg bovitesre var.
- A PDF szamla workflow manualis review alapu; OCR/adatkinyeres meg nincs kesz.
- A theoretical stock controlling becsles, nem fizikai raktarprogram es nem FIFO valuation.
- A dashboard brutto/netto/AFA jelolese elkezdodott, de a POS oldali derived netto/AFA pipeline meg tovabbi munka.
- A forecast jelenleg baseline alapu, nem fejlett prediktiv ML.
- A Flow event settlement lite meg nem teljes elszamolasi motor.

## 8. Jovobeli fejlesztesi teruletek

Prioritasos jovobeli iranyok:

1. POS mapping es missing recipe/missing cost munkalistak tomeges kezelese.
2. PDF beszerzesi szamla OCR/adatkinyeres, majd kotelezo emberi review.
3. Teljesebb netto/brutto/AFA reporting beveteli es kiadasi oldalon.
4. Receptverzio, publikacio, sablonos receptinditas es tomeges javitas.
5. Inventory controlling melyites: ok- es item-szintu dontesi javaslatok.
6. Flow event elszamolas melyitese: ticket/bar late binding, performer share, fixed fee, event cost.
7. Gourmand dashboard melyites: recept, keszlet, weather es elokeszitesi javaslat.
8. Statisztikai alapok: median, percentilisek, szoras, rolling average, mozgo median.
9. Anomalia detektalas: szokatlan forgalom, keszletelteres, termekvisszaeses.
10. Predikcios modellek: pesszimista/realista/optimista savok, regression, Bayes-i frissites, scenario planning.
11. Kesobbi ML modellek: demand forecasting, basket recommendation, event performance prediction, stockout risk.

## 9. Vedesi szempontbol kiemelheto lenyeg

A BizTracker legfontosabb szakmai erteke nem az, hogy admin CRUD feluleteket ad, hanem hogy egy valos uzleti folyamatot adatbizalmi retegekre bont:

```text
forrasadat -> validalas -> dedupe -> mapping -> actual/estimated/derived szetvalasztas -> read model -> dontestamogatas
```

A rendszer technikai oldalon clean architecture iranyba rendezett modularis monolit, uzleti oldalon pedig controlling es adattudomanyi szemleletu elemzo alkalmazas. A szamitasok explicit modon kovethetoek: latszik, hogy a bevetel POS actualbol, a COGS recept/default cost alapu becslesbol, a keszlet variance actual movement es theoretical quantity kulonbsegebol, az event profit pedig ticket/bar/performer/cost komponensekbol epul.

Ezert a program vedeseben kulon hangsulyozhato, hogy az alkalmazas nem csak adatokat tarol, hanem adatminosegi allapotokat, forraslineage-et, validacios szabalyokat es dontesi jelzeseket is kezel.
