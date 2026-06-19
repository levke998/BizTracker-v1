# BizTracker fejlesztes tobb geprol

Ez az utmutato azt a modellt koveti, hogy a kod GitHubon van, minden fejlesztoi
gep sajat PostgreSQL adatbazist hasznal, az adatbazis szerkezetet az Alembic
migraciok, az alapadatokat pedig az idempotens bootstrap allitja elo.

Egyetlen kozos fejlesztoi DB hasznalata nem ajanlott: a migraciok, integration
tesztek es felkesz fejlesztesek osszeakadhatnak. Ha ugyanaz az uzleti adathalmaz
kell ket gepen, dump/restore snapshotot kell hasznalni.

## 1. Git es GitHub

1. Telepitsd a GitHub Desktopot, jelentkezz be, majd klonozd:
   `https://github.com/levke998/BizTracker-v1.git`
2. Ellenorizd uj PowerShell ablakban:

```powershell
git --version
git status
git remote -v
```

A GitHub Desktop nem `.env` valtozo. A `git.exe` konyvtaranak a felhasznaloi
`PATH`-ban kell lennie, vagy kulon Git for Windows telepites hasznalhato.

Fejlesztes elott mindig:

```powershell
git pull --ff-only
```

Gepvaltas elott minden kesz valtozast commitolj es pusholj. Felkesz munka
atadasara kulon branch ajanlott.

## 2. Szoftverek az uj gepen

- Python 3.12 vagy ujabb kompatibilis 3.x verzio
- Node.js es npm
- PostgreSQL 18, vagy Docker Desktop
- GitHub Desktop vagy Git for Windows

## 3. PostgreSQL inditasa

### A lehetoseg: Docker Desktop

A repository gyokereben:

```powershell
docker compose up -d db
docker compose ps
```

Ehhez a `backend/.env` adatbazis sora:

```text
DATABASE_URL=postgresql+psycopg://biztracker:biztracker_dev@localhost:5432/biztracker
```

Ha a gepen mar masik PostgreSQL hasznalja az 5432 portot:

```powershell
$env:BIZTRACKER_DB_PORT=5433
docker compose up -d db
```

Ekkor a `DATABASE_URL` portja is `5433` legyen.

### B lehetoseg: natív PostgreSQL

Hozz letre egy `biztracker` adatbazist es egy sajat fejlesztoi felhasznalot,
majd annak adatait ird a `backend/.env` `DATABASE_URL` ertekebe. A `.env`
lokalis titok, Gitre nem kerulhet.

## 4. Projekt inicializalasa

Backend:

```powershell
cd backend
Copy-Item .env.example .env
python -m pip install -e ".[dev]"
python -m alembic upgrade head
python -m scripts.bootstrap_reference_data
python -m alembic current
```

Az `.env` masolasa utan csereld le legalabb a `SECRET_KEY`, az admin jelszo es
szukseg eseten a `DATABASE_URL` erteket.

Frontend:

```powershell
cd ..\frontend
npm.cmd ci
Copy-Item .env.example .env
npm.cmd run build
```

## 5. Ures fejlesztoi DB vagy azonos adatsnapshot

Altalaban az ures, migralt es bootstrapelt DB a jobb valasztas. Igy a fejlesztes
reprodukalhato, es egyik gep sem irja felul a masik munkajat.

Ha ugyanaz az aktualis adathalmaz kell a masik gepen, a forrasgepen:

```powershell
cd backend
python -m scripts.backup_database
```

Az eredmeny a `backend/backups` konyvtarba kerul. A dump uzleti vagy szemelyes
adatot tartalmazhat, ezert:

- ne commitold es ne toltsd fel a repositoryba;
- titkositott felhot, titkositott archivumot vagy biztonsagos adathordozot
  hasznalj az atvitelhez;
- az importalt fajlok ujrafeldolgozasahoz a `backend/storage` tartalmat is
  kulon, biztonsagosan masold at.

A celgepen, a helyes `backend/.env` beallitasa es a PostgreSQL inditasa utan:

```powershell
cd backend
python -m scripts.restore_database C:\secure\biztracker-YYYYMMDD-HHMMSS.dump `
  --confirm-database biztracker
python -m alembic upgrade head
```

A restore torli es lecsereli a celadatbazis azonos objektumait. A script
alapertelmezetten csak helyi adatbazisra engedi ezt.

## 6. Napi gepvaltas

Munka megkezdese:

```powershell
git pull --ff-only
cd backend
python -m alembic upgrade head
```

Munka befejezese:

```powershell
git status
git add <fajlok>
git commit -m "Rovid, ertelmes leiras"
git push
```

Az adatbazis dumpot nem kell minden gepvaltaskor mozgatni. Csak akkor keszits
uj snapshotot, ha az aktualis lokalis adatok tenylegesen szuksegesek a masik
gepen. Az adatbazis semmilyen korulmenyek kozott nem helyettesiti a migraciot:
minden schema-valtozas Alembic migration legyen es keruljon Gitre.

## 7. Teljes lokalis validacio

A repository gyokerebol:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\validate.ps1
```

A script:

- elinditja es healthcheckkel ellenorzi a helyi PostgreSQL kontenert;
- lefuttatja a DB-fuggetlen unit teszteket;
- minden futasnal ujraletrehozza a kulon `biztracker_test` adatbazist;
- migraciot es referenciaadat-bootstrapot futtat a tesztadatbazison;
- szekvencialisan lefuttatja az integration teszteket;
- kulon, Git-altal ignoralt konyvtarba kesziti el a frontend ellenorzo buildet.

A helyi `biztracker` adatbazisban levo Gourmand/Flow snapshotot a validacio nem
modositja. Gyorsabb, reszleges ellenorzes:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\validate.ps1 -SkipIntegration
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\validate.ps1 -SkipFrontend
```
