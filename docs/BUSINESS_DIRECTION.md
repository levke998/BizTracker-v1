# BizTracker Business Direction

Ez a dokumentum a projekt aktualis uzleti iranyat rogziti. A cel, hogy a technikai roadmap ne szakadjon el attol, amiert a rendszer keszul: a `Gourmand` es a `Flow Music Club` uzleti elemzesetol es dontestamogatasatol.

Kapcsolodo dokumentumok:
- [PROJECT_DESCRIPTION.md](C:\BizTracker\PROJECT_DESCRIPTION.md)
- [CURRENT_STATUS.md](C:\BizTracker\docs\CURRENT_STATUS.md)
- [ROADMAP.md](C:\BizTracker\docs\ROADMAP.md)
- [ACCOUNTING_AND_CONTROLLING_MODEL.md](C:\BizTracker\docs\ACCOUNTING_AND_CONTROLLING_MODEL.md)
- [THEORETICAL_STOCK_PREPARATION.md](C:\BizTracker\docs\THEORETICAL_STOCK_PREPARATION.md)

## 1. A rendszer fo celja

A BizTracker nem altalanos admin felulet, hanem ket konkret uzlet uzleti elemzo es controlling rendszere:
- `Gourmand`
- `Flow Music Club`

A legfontosabb kerdesek, amikre a rendszernek valaszolnia kell:
- mennyi a bevetel
- mennyi a kiadas
- mennyi a profit
- mibol tevodik ossze a forgalom
- mit vettek a vasarlok
- mennyit vettek
- mennyi az atlagkosar
- mely termekek es kategoriak mennek jol
- hogyan valtozik a teljesitmeny idoben

Az inventory, a finance, az import es a kesobbi predikcio mind ezt a fo celt tamogatja.

## 2. Mi a szerepe az inventorynak ebben a rendszerben

Az inventory onmagaban nem a vegcel, hanem egy fontos gazdasagi es operationalis alapreteg.

Az inventory szerepe:
- tamogatja a kiadasok es keszleten allo penz ertelmezeset
- alapot ad a profit es margin jobb becslesehez
- megalapozza a kesobbi FIFO costingot
- alapot ad a kesobbi predikcios modellekhez

Kulcselv:
- az inventory fontos, de a rendszer elsodleges nezoPontja tovabbra is az uzleti teljesitmeny elemzese

## 3. Sales-driven filozofia

Kiemelten fontos uzleti pontositas:

A cukraszda oldalon nem biztos, hogy pontosan tudjuk, mennyi kesztermek keszul el. Amit biztosan tudunk:
- mit adtunk el
- mennyit adtunk el

Ezert a rendszer inventory management szemlelete:
- az egyik legerosebb igazsagforras az eladas, tehat a kasszaforgalom
- a theoretical / estimated inventory ennek alapjan epul
- a modellnek keszen kell allnia arra is, hogy ha egyszer lesz realtime kesztermek-ellenorzes vagy pontosabb operativ adat, azt kesobb be tudjuk fogadni

Tehat:
- most sales-driven es import-driven iranyban haladunk
- kesobb bovitheto realtime vagy pontosabb kesztermek kovetessel

Ez kulonosen a Gourmand oldalon fontos.

## 4. Mit tudunk biztosan importalni

Jelenleg biztosnak tekintheto:

### Forgalmi adatok
Mindket uzlet kasszaprogramja tud:
- CSV exportot
- Excel exportot

Es valoszinuleg:
- API kapcsolattal is elerheto

De:
- az API eleres jelenleg meg nincs a kezunkben

Ezert a fejlesztes helyes sorrendje:
1. file import stabilitasa
2. domain mapping
3. kesobb API connector

### Rendelesek / szamlak
A rendeleseket es beszerzeseket ket iranyban kell kezelnunk:
- PDF feltoltes
- teteles manualis rogzitese

Ez kulonosen fontos a kesobbi:
- inventory novekedeshez
- koltsegoldali controllinghoz
- FIFO alapokhoz

## 5. Dashboard-first vegcel

A vegso rendszer dashboard alapu lesz.

A cel nem egyetlen statikus dashboard, hanem egy olyan analitikai felulet, ahol:
- KPI csempek vannak
- diagramok vannak
- interaktiv drill-down van
- minden lenyeges mutato lebontHato a legelemibb szintig

Pelda irany:
- revenue
- revenue megoszlas
- mibol tevodik ossze
- melyik category
- melyik product
- melyik transaction

Ez az a vegcel, amihez a jelenlegi minimalis frontend oldalak fokozatosan kozelitenek.

## 6. Kiemelt menu-irany

Az alkalmazas hosszabb tavu fo menustrukturaja:

### Overall
- osszesitett uzleti nezet
- KPI csempek
- diagramok
- bevetelek es megoszlasok
- interaktiv bontas

### Flow Music
- ugyanennek az uzlet-specifikus nezetnek a Flow-ra szukitett valtozata
- kesobb event szervezes es event profitability

### Gourmand
- ugyanennek az uzlet-specifikus nezetnek a Gourmandra szukitett valtozata

### Inventory
- Flow
- Gourmand
- esetleg kesobb osszesitett inventory kimutatas

### Feltoltes
- szamla feltoltes
- forgalom feltoltes
- kesobbi harmadik upload workflow

A jelenlegi oldalak ezeknek az iranyoknak a technikai elokeszitesei.

## 7. Upload filozofia

Az upload modul nem segedoldal, hanem az egyik kulcs belso workflow.

Rovid tavon legalabb ezekre kell epulnie:

1. `Szamla feltoltes`
   - PDF vagy manualis teteles felvitel
   - beszerzes
   - koltseg
   - inventory novekedes
   - FIFO alap

2. `Forgalom feltoltes`
   - CSV / Excel forgalmi adat
   - ha nincs realtime API, ez a fo adatbeviteli ut

3. `Kesobbi harmadik workflow`
   - ide olyan importok johetnek, mint event adatok, settlement, vagy mas strukturalt uzleti input

## 8. Időjárás és üzleti minták

Az idojaras kulonosen a Gourmand oldalon fontos elemzesi tenyezo lehet.

Celpont:
- Szolnok idojaras adatok rogzitese
- kesobb osszekapcsolni az ertekesitesi adatokkal
- mintakat keresni

Pelda:
- jo, meleg, napos ido -> erosebb fagylalt ertekesites

Fontos:
- nem transaction-szintu idojaras rogzitest akarunk
- inkabb kb. 3 oras vagy hasonlo elemzesi ablakokat

Ez mar jobban illeszkedik a controlling es predikcios retegekhez.

## 9. Fejlesztesi elv innen tovabb

Most mar nem a nullarol epitunk, hanem fokozatosan bontjuk ki a meglevo minimalis szeleteket.

Ezert minden kovetkezo fejlesztesnel tartsuk ezt szem elott:
- a rendszer fo celja a business analysis
- az inventory es finance ezt tamogatja
- a dashboard vegcelhez kell igazodni
- az actual es estimated retegek nem keverhetok
- az import irany valos uzleti workflow marad

## 10. Gyakorlati kovetkezmeny a kovetkezo feladatokra

A kovetkezo fejleszteseknel ezt jelenti:
- inventory movement frontend flow fontos, mert az operativ valosagot epiti
- procurement foundation fontos, mert a kiadasok es inventory novekedes alapja
- upload modul bovites fontos, mert a valos uzleti adat innen jon
- overall / business dashboard iranyt mar most tudatosan kell epiteni

Rovid osszefoglalo:
- az inventory fontos, de nem vegcel
- az eladas az egyik legerosebb igazsagforras
- a rendszer sales-driven es controlling-driven
- a vegso forma dashboard es drill-down alapu uzleti elemzo rendszer
