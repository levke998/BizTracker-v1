# BizTracker Accounting And Controlling Model

Ez a dokumentum a BizTracker uzleti controlling es operativ penzugyi modelljenek elso strukturalt leirasat rogzitI. A cel nem egy teljes szamviteli vagy konyvelesi motor megvalositasa, hanem egy tiszta, magyarazhato, bovitheto gazdasagi modell lefektetese, amelyre kesobb pontosabb szamviteli logika is raepitheto.

Kapcsolodo dokumentumok:
- [PROJECT_DESCRIPTION.md](C:\BizTracker\PROJECT_DESCRIPTION.md)
- [ARCHITECTURE.md](C:\BizTracker\docs\ARCHITECTURE.md)
- [CURRENT_STATUS.md](C:\BizTracker\docs\CURRENT_STATUS.md)
- [BUSINESS_DIRECTION.md](C:\BizTracker\docs\BUSINESS_DIRECTION.md)
- [IMPORT_PROFILES.md](C:\BizTracker\docs\IMPORT_PROFILES.md)

## 1. A rendszer alapelve

### Mi a rendszer celja

A BizTracker egy belso uzleti controlling es operativ penzugyi modellre epulo rendszer. A fo cel:
- a ket vallalkozas uzleti teljesitmenyenek ertheto kovetese
- a bevetel, koltseg, profit es keszlethelyzet magyarazhato modellezese
- a napi operativ dontesek tamogatasa
- a kesobbi riporting, analitika es predikcio megalapozasa

Ez a modell elsosorban uzleti igazsagot akar adni, nem jogszabalyi szintu konyvelesi igazsagot.

### Mi NEM a cel

Nem cel jelenleg:
- teljes konyvelesi rendszer
- fo konyvi konyveles
- kettos konyvvitel teljes lekepzese
- hivatalos adozasi vagy beszamolasi logika
- teljes accounting engine

Vagyis a rendszer nem konyvelo program, hanem controlling es dontestamogato rendszer.

### Hogyan marad bovitheto

A bovithetoseget ezek biztosItjak:
- clean architecture
- modulonkenti szeparacio
- SOLID elvek
- actual, estimated es analytical retegek kulonvalasztasa
- konfiguralt szabalyok hasznalata hardcode helyett ott, ahol uzletileg valtozhat a logika

Ez azt jelenti, hogy a jelenlegi egyszerusitett modell kesobb finomithato anelkul, hogy az alapveto domain hatarokat ujra kellene rajzolni.

## 2. A modell 4 fo retege

### 1. Financial actuals

Ez a legfontosabb penzugyi igazsagforras.

Ide tartoznak azok a tenyleges penzugyi esemenyek, amelyek bevetelt vagy koltseget jelentenek, peldaul:
- POS sales
- supplier invoice
- ticket revenue
- bar revenue
- performer fee
- egyeb koltsegek

Ebbol lesznek a controlling alapmutatok:
- revenue
- cost
- profit

Fontos elv: ami itt szerepel, az penzugyi tenynek tekintheto.

### 2. Operational actuals

Ez az operativ valosag retege.

Ide azok az esemenyek tartoznak, amelyek tenylegesen megtortenek a keszlettel vagy az uzemeltetessel:
- beszerzes
- manualis keszletbeallitas
- leltar
- selejt
- korrekcio

Ez a retege lehet hianyos. Ez nem problema, hanem a valos uzleti elet resze. A rendszernek azt kell tudnia kezelni, hogy nem minden mozgast rogzitunk tokeletesen az MVP-ben.

### 3. Estimated / modeled layer

Ez a rendszer legfontosabb intelligens retege.

Ide tartoznak:
- recept alapu fogyasbecsles
- eladas alapu becsult keszletfogyas
- koltsegkalkulacio
- margin becsles
- reorder javaslat
- theoretical stock

Ez a retege nem teny, hanem modellalt vagy szarmaztatott adat. Ettol lesz a rendszer hasznos uzletileg, de ezt mindig kulon kell kezelni a tenyleges adatktol.

### 4. Analytical snapshots

Ez a riport es dashboard retege.

Ide tartoznak:
- KPI csempek
- grafikonok
- drill-down nezetek
- idoszaki snapshotok
- aggregalt riportok

Ez a reteg mar nem operativ igazsag, hanem elemzesi es megjelenitesi reteg.

### Kulcselv: actual vs estimated

Az egyik legfontosabb tervezesi alapelv:
- `actual` != `estimated`

Minden fontos adatot ugy kell modellezni es kommunikani, hogy vilagos legyen:
- `actual`
- `estimated`
- `derived`

Ez teszi a rendszert magyarazhatova es hitelesse.

## 3. Inventory modell

### Physical vs theoretical stock

Az inventory modell ket parhuzamos igazsagot kezel:

1. `physical / actual stock`
   Ez az, amit valoban tudunk a keszletrol:
   - beszerzes
   - leltar
   - manualis korrekcio
   - selejt

2. `theoretical stock`
   Ez az, amit a modell szamol:
   - beszerzes
   - becsult felhasznalas
   - eladas alapu fogyas

A ketto kozti kulonbseg nem hiba, hanem uzleti insight:
- selejt
- lopas
- recept elteres
- rogzitett es tenyleges mukodes kozti elteres

### Beszerzes es keszletnovekedes

Az inventory actual oldalan a keszletnovekedes alapja a beszerzes. Ez adja a kesobbi keszletertekeles egyik fo bemeneti pontjat.

### Eladas alapu becsult fogyas

Kulonosen a Gourmand eseteben az eladas sokszor nem egy az egyben inventory mozgaskent jelenik meg. Ilyenkor a rendszer:
- az eladast tenykent kezeli
- a recept alapjan becsult fogyast szamol

Ez estimated reteg, nem actual keszletmozgas.

### Elteresek jelentese

A rendszernek kesobb ertelmezni kell tudnia az eltereseket:
- selejt
- lopas
- recepttol valo eltavolas
- keszletkorrekcio

Ezek az elteresek controlling szempontbol fontosabbak lehetnek, mint a nyers keszletszam.

### Keszleten allo penz

Az inventory valuation egyik fo controlling kerdes:

`inventory_value = sum(remaining_qty * cost_basis)`

Ez a keszleten allo penz alapelve. Az MVP-ben ez meg egyszerusitett koltsegkezelessel indulhat, de a modell mar most ugy legyen felepitve, hogy kesobb pontosithato legyen.

### FIFO-ra valo felkeszites

Celpont:
- FIFO-compatible inventory modell

MVP:
- egyszerusitett koltsegkezeles
- kesobbi FIFO-hoz alkalmas adatmodell

Kesobb:
- kulon FIFO consumption layer
- pontosabb COGS szamitas
- pontosabb inventory valuation

Kulcselv:
- most nem kell teljes FIFO engine
- de a modell ne zarja ki a FIFO-t

## 4. Gourmand uzleti modell

### Product vs inventory item

A Gourmand eseteben kulon kell kezelni:
- `product`
  amit eladunk
- `inventory item`
  amit tarolunk, felhasznalunk, beszerzunk

Ez a kulonvalasztas alapveto. Nem minden product inventory item, es nem minden inventory item product.

### Recipe / BOM szerepe

A recipe vagy BOM a Gourmand modell magja. Ez mondja meg:
- milyen alapanyagok szuksegesek
- milyen mennyisegben
- milyen yield mellett

A recipe nem csak gyartasi, hanem controlling objektum is.

### Eladas alapu fogyas szamitas

A logika:

`sales -> estimated usage -> recipe -> cost -> margin`

Tehat:
- az eladas teny
- a felhasznalas recept alapu becsles
- ebbol szamolhato az estimated COGS

Fontos gyakorlati pontositas:
- nem biztos, hogy pontosan tudjuk, mennyi kesztermek keszul el
- amit biztosan tudunk, az az eladas

Ezert a Gourmand oldalon a rendszernek sales-driven inventory szemleletre kell epulnie:
- a kassza forgalom eros truth source
- a kesobbi theoretical stock es estimated consumption erre epul
- de a modell maradjon nyitott arra, hogy ha kesobb pontosabb kesztermek vagy realtime ellenorzes jon, azt be tudjuk fogadni

### Estimated COGS

A Gourmand eseteben a COGS sokszor becsles:
- eladott mennyiseg
- recipe version
- ingredient cost basis

Ez kezdetben estimated COGS, nem teljes accounting COGS.

### Margin szamitas

Egyszerusitett uzleti keplet:

`margin = selling price - estimated cost`

Ez controlling celra mar hasznos, akkor is, ha kesobb pontositani kell.

### Darabos es suly alapu termekek

Kritikus kulonbseg:
- darabos termek
- suly alapu termek

Pelda:
- croissant: darabos
- pogacsa: suly alapu

Ezert a modellnek kesobb kezelnie kell:
- `selling_unit_type`
- `recipe_yield`

### Recipe yield

Pelda:
- `1 adag teszta -> 2.4 kg pogacsa`

Ez a yield kapcsolat teszi lehetove, hogy az eladas alapjan ertelmes becsles keszuljon a felhasznalasrol es a koltsegrol.

### Recept valtozas hatasa

Ha a recept valtozik:
- az uj recipe version uj becslest eredmenyez
- a tortenelmi adatokat a korabeli recipe version szerint kell ertelmezni

Ezert a recipe verziok kovetese nem opcionaIis uzleti pontossagi szempontbol.

## 5. Flow uzleti modell

### Event es bar kulon kezelese

A Flow eseteben ket kulon vilagot kell kezelni:

1. `event`
   - ticket revenue
   - performer szabalyok
   - event cost

2. `bar`
   - POS sales
   - inventory consumption

Ezt a ketto nem szabad koran osszemosni.

### Ticket revenue

Az event oldali jegybevetel financial actual. Ez az egyik fo bemenet az event profitability modellhez.

### Bar revenue

A bar oldal revenue-ja szinten financial actual, de logikailag kulon kezelendo, mert mas koltseg- es fogyasmodell tartozik hozza.

### Event cost

Ide tartozhat:
- performer fee
- technikai koltsegek
- marketing
- egyeb event-specifikus kiadasok

### Performer modell

A performer elszamolas konfiguralt szabaly legyen, ne hardcode.

Pelda:
- revenue share `80%`

Ez lehet:
- fixed fee
- revenue share
- kesobb hibrid szabaly

Kulcselv:
- a performer rule konfiguralt domain szabaly legyen
- ne kodba egetett magic number

### Event profit modell

Egyszerusitett controlling szemlelet:

`retained_ticket_revenue + bar_revenue - event_cost = event_profit`

Ahol:
- `ticket_revenue`
- `performer_share`
- `retained_ticket_revenue`
- `bar_revenue`
- `event_cost`

Kulon fogalmak legyenek, hogy a rendszer magyarazhato maradjon.

## 6. Estimated vs actual filozofia

### Mit tekintunk tenynek

Teny:
- eladas
- szamla
- ticket revenue
- bar revenue
- beszerzes
- leltar
- manualis korrekcio

### Mit tekintunk becslesnek

Becsles:
- recept alapu fogyas
- eladas alapu alapanyag-felhasznalas
- estimated COGS
- theoretical stock
- reorder javaslat

### Hogyan lesz a rendszer magyarazhato

A rendszer akkor magyarazhato, ha minden fontos KPI moge oda lehet tenni:
- milyen tenyadatokbol szamol
- milyen becsleseket hasznal
- milyen szabalyok alapjan vezeti le a kovetkeztetest

Ez kulonosen fontos:
- dashboardoknal
- margin riportoknal
- keszleteltereseknel
- event profitability riportoknal

### Miert fontos ez a kesobbi analitikahoz

Ha az actual es estimated reteg keveredik:
- az analitika elveszti a hitelesseget
- a felhasznalo nem fogja tudni, mit nez
- a kesobbi predikcio hibas alapra epul

Ha viszont tisztan kulonvalnak:
- a riportok megbizhatoak
- a becslesek magyarazhatoak
- a kesobbi modellfejlesztes biztonsagosabb

## 7. UI es analitika koncepcio

### Cel UX

A cel egy olyan UI, ahol az uzleti felhasznalo:
- gyorsan atlatja a fo KPI-kat
- tud szurni minden lenyeges dimenziora
- tud drill-downolni az osszesitett nezetekbol

### KPI csempek

Tipikus KPI-k:
- revenue
- cost
- profit
- margin
- inventory value
- event profit

### Grafikonok

Tipikus vizualizaciok:
- idosoros revenue trend
- category mix
- product performance
- event profitability
- estimated vs actual elteresek

### Drill-down

Kulcselv:
- minden aggregalt adat legyen visszavezetheto reszletekre

Pelda:

`revenue -> category -> product -> transaction`

Ugyanez kesobb:

`inventory value -> item -> movement / estimate source`

### Szures minden szinten

Alap szurok:
- business unit
- datum
- category
- product
- event
- transaction type
- actual vs estimated

## 8. Keszleten allo penz es COGS

### Inventory valuation alapelve

A keszleten allo penz controlling szemleletben azt mutatja meg, mennyi ertek all keszletben.

Egyszerusitett keplet:

`inventory_value = sum(remaining_qty * cost_basis)`

### Estimated consumption alapu koltseg

A Gourmand es kesobb a bar oldal egyes reszein a koltseg kezdetben gyakran estimated lesz:
- sales alapu fogyasbecsles
- recipe vagy consumption rule
- egyszerusitett cost basis

Ez mar most is hasznos controlling informacio, meg akkor is, ha nem accounting pontossagu.

### Kesobbi pontositas lehetosege

Kesobb bovitheto:
- FIFO costing
- batch-level inventory valuation
- pontosabb purchase cost lekovetes
- inventory adjustment modellek
- PDF es manualis beszerzesi workflow-k strukturaltabb bekotese

Kulcselv:
- az MVP-ben egyszeru
- a modellben kesobb pontosithato

## 9. Jovobeli bovitesi iranyok

Rovid, de logikus kovetkezo iranyok:
- recipe kezeles
- inventory movement
- FIFO costing
- event settlement finomitas
- weather-based es sales-based predikcio
- POS API kapcsolat, ha az eleres konkretan rendelkezesre all

Ezeket most nem kell tulreszletezni. A lenyeg, hogy a mostani modell ne allja utjukat.

## 10. RovId osszefoglalo

A BizTracker lenyege egy olyan uzleti controlling es operativ modell, amely:
- tenyekre epul
- kulon kezeli a becsleseket
- magyarazhato riportokat ad
- fokozatosan bovitheto pontosabb gazdasagi logika iranyaba

Ettol lesz ertekes:
- mar MVP szinten tud uzleti insightot adni
- nem keveri ossze a tenyt es a modellt
- fejlesztoknek es uzleti oldalnak is ertelmezheto marad

A kovetkezo implementacios fokusz:
- inventory movement write alap
- erre epulve stock level szemlelet
- kesobb recipe es pontosabb estimated consumption
