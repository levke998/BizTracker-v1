# BizTracker Architecture

Ez a dokumentum a BizTracker induló projektarchitektúráját rögzíti. A cél egy olyan stabil, moduláris alap kialakítása, amely alkalmas valós üzleti működés támogatására, de nem overengineerelt.

Kapcsolódó dokumentum:
- [PROJECT_DESCRIPTION.md](C:\BizTracker\PROJECT_DESCRIPTION.md)
- [MVP_IMPLEMENTATION_PLAN.md](C:\BizTracker\docs\MVP_IMPLEMENTATION_PLAN.md)
- [MIGRATION_PLAN.md](C:\BizTracker\docs\MIGRATION_PLAN.md)
- [IDENTITY_CORE_MODEL_PLAN.md](C:\BizTracker\docs\IDENTITY_CORE_MODEL_PLAN.md)

## 1. Architektúra célja

Az alkalmazás két eltérő, de részben közös üzleti domaint kezel:
- `Gourmand Sütőház és Kézműves Cukrászat`
- `Flow Music Club`

Az induló technikai irány:
- backend: `FastAPI`
- frontend: `React + TypeScript`
- adatbázis: `PostgreSQL`
- architektúra: `moduláris monolit`

Ez a döntés azért ajánlott, mert:
- tiszta modulhatárokat ad,
- gyorsabb indulást tesz lehetővé, mint egy microservice-rendszer,
- később is felbontható marad,
- jól támogatja a clean architecture szemléletet.

## 2. Fő architekturális elvek

- a rendszer `operatív` és `analitikai` funkcióit logikailag el kell különíteni
- az üzleti modulok legyenek egymástól világosan szeparálva
- az infrastruktúra ne szivárogjon közvetlenül a domainbe
- a backend legyen use case orientált, ne csak CRUD-központú
- a frontend legyen route-alapú feature modulokból felépítve
- a legtöbb állapot a backendből érkezzen, ne a kliensben duplikáljuk

## 3. Repository szintű szerkezet

```text
BizTracker/
  PROJECT_DESCRIPTION.md
  docs/
    ARCHITECTURE.md
    INITIAL_STRUCTURE.md
    IDENTITY_CORE_MODEL_PLAN.md
    MVP_IMPLEMENTATION_PLAN.md
    MIGRATION_PLAN.md
  backend/
    app/
    migrations/
    tests/
    pyproject.toml
    alembic.ini
    .env.example
  frontend/
    src/
    public/
    package.json
    vite.config.ts
    tsconfig.json
    .env.example
```

## 4. Backend architektúra

### 4.1. Backend gyökérstruktúra

```text
backend/
  app/
    api/
    core/
    db/
    shared/
    modules/
  migrations/
    versions/
  tests/
    unit/
    integration/
```

### 4.2. Backend mappák felelőssége

#### `app/`
Az alkalmazás teljes futó kódja.

#### `app/api/`
Globális, moduloktól független API elemek.

Felelősség:
- root router összeállítás
- health check endpointok
- rendszer-szintű routing

#### `app/core/`
Keresztmetszeti technikai elemek.

Felelősség:
- konfiguráció
- security
- auth helper
- dependency wiring
- logging

#### `app/db/`
Adatbázis inicializációs és session kezelés.

Felelősség:
- SQLAlchemy base
- engine és session factory
- model registry

#### `app/shared/`
Modulok között megosztott, nem domain-specifikus elemek.

Felelősség:
- közös enumok
- közös DTO-k vagy helper osztályok
- cross-module utility-k

#### `app/modules/`
Minden üzleti modul külön alkönyvtárban él.

Modulok:
- `identity`
- `master_data`
- `inventory`
- `finance`
- `procurement`
- `production`
- `events`
- `imports`
- `analytics`

### 4.3. Modulon belüli clean architecture szerkezet

Minta:

```text
app/modules/inventory/
  presentation/
    api/
    schemas/
    dependencies.py
  application/
    commands/
    queries/
    services/
    dto/
  domain/
    entities/
    value_objects/
    repositories/
    services/
    exceptions.py
  infrastructure/
    orm/
    repositories/
    mappers/
```

#### `presentation/`
HTTP réteg.

Felelősség:
- route-ok
- request/response sémák
- auth és permission dependency-k
- query param és body validáció

#### `application/`
Use case réteg.

Felelősség:
- parancsok és lekérdezések kezelése
- tranzakciós műveletek koordinálása
- domain és repository együttműködés szervezése
- DTO-k előállítása

#### `domain/`
Üzleti mag.

Felelősség:
- entitások
- value objectek
- üzleti szabályok
- domain service-ek
- repository interfészek

#### `infrastructure/`
Technikai megvalósítás.

Felelősség:
- ORM modellek
- repository implementációk
- külső integrációk
- mapperek

### 4.4. Backend modulok rövid szerepe

#### `identity`
- bejelentkezés
- tokenkezelés
- felhasználók, szerepkörök, jogosultságok

#### `master_data`
- business unit
- location
- unit of measure
- category
- product

#### `inventory`
- készletelemek
- raktárak
- készletmozgások
- készletszámítás

#### `finance`
- bevétel és kiadás
- pénzügyi tranzakciók
- pénzügyi összesítések

#### `procurement`
- beszállítók
- beszerzések
- számlák

#### `production`
- receptek
- receptverziók
- gyártási batch-ek
- alapanyag-felhasználás

#### `events`
- események
- fellépők
- jegy- és bárbevétel
- eseményköltségek

#### `imports`
- CSV/Excel import
- későbbi API importok
- staging
- import naplózás és hibakezelés

#### `analytics`
- dashboard read modellek
- aggregációs lekérdezések
- összehasonlító riportok

## 5. Frontend architektúra

### 5.1. Frontend gyökérstruktúra

```text
frontend/
  src/
    app/
    routes/
    modules/
    shared/
    services/
    hooks/
    lib/
    types/
    styles/
    main.tsx
  public/
```

### 5.2. Frontend mappák felelőssége

#### `src/app/`
App assembly.

Felelősség:
- provider-ek
- app shell
- router bootstrap

#### `src/routes/`
Központi route-definíciók.

Felelősség:
- route tree
- protected route logika
- layout binding

#### `src/modules/`
Feature-alapú frontend modulok.

Minden modul jellemzően tartalmaz:
- `pages/`
- `components/`
- `api/`
- `hooks/`
- `types/`

#### `src/shared/`
Modulok között újrahasznosítható UI és utility elemek.

#### `src/services/`
Közös API kliens és állapotlekérő infrastruktúra.

#### `src/hooks/`
Globálisan használt hookok.

#### `src/lib/`
Általános technikai utility-k.

#### `src/types/`
Közös TypeScript típusok.

#### `src/styles/`
Globális stílusok és tokenek.

### 5.3. Frontend feature modul minta

```text
src/modules/inventory/
  pages/
    InventoryListPage.tsx
    StockLevelsPage.tsx
  components/
    InventoryTable.tsx
  api/
    inventoryApi.ts
  hooks/
    useInventoryItems.ts
  types/
    inventory.ts
```

### 5.4. State management javaslat

Javasolt felosztás:
- `TanStack Query`: szerveroldali állapot
- `Zustand`: kis globális kliensoldali állapot
- `React local state`: lokális UI állapot

Mi kerüljön ide:
- `TanStack Query`: listák, részletek, dashboardok, cache
- `Zustand`: auth session, kiválasztott business unit, globális szűrők ha kell
- helyi state: formok átmeneti állapota, modálok, tabok

## 6. Adatbázis kapcsolat

Ajánlott megoldás:
- `SQLAlchemy 2.x`
- közös engine
- request-scope session FastAPI dependency-vel
- repository-alapú adatelérés

Fő fájlok:
- `backend/app/db/session.py`
- `backend/app/db/base.py`
- `backend/app/core/dependencies.py`

Elv:
- a session a presentation/application rétegen keresztül jusson a use case-ekhez
- a domain ne ismerje az ORM részleteit

## 7. Migration kezelés

Ajánlott eszköz:
- `Alembic`

Fő fájlok:
- `backend/alembic.ini`
- `backend/migrations/env.py`
- `backend/migrations/versions/`
- `backend/app/db/models_registry.py`

Elv:
- autogenerate használható, de minden migrationt kézzel ellenőrizni kell
- az ORM modellek regisztrációja legyen centralizált
- a sémák kezelése legyen explicit: `auth`, `core`, `ingest`, `analytics`

## 8. Auth kezelés

Ajánlott induló irány:
- JWT access token
- refresh token
- role és permission alapú authorization

Backend fő fájlok:
- `backend/app/core/security.py`
- `backend/app/core/auth.py`
- `backend/app/modules/identity/...`

Frontend fő fájlok:
- `frontend/src/services/storage/tokenStorage.ts`
- `frontend/src/routes/protected.tsx`
- `frontend/src/modules/identity/...`

Elv:
- az auth modul legyen különálló
- az authorization ne keveredjen a route logikába szétcsúszva
- a permission ellenőrzés legyen újrahasznosítható dependency/helper

## 9. Konfiguráció és `.env`

Backend:
- `pydantic-settings`

Frontend:
- `Vite env`

Elv:
- a valódi secret ne kerüljön verziókezelésbe
- csak `.env.example` legyen commitolva
- a config kulcsok központi helyen legyenek definiálva

Példa backend kulcsok:
- `APP_ENV`
- `APP_NAME`
- `API_V1_PREFIX`
- `SECRET_KEY`
- `DATABASE_URL`
- `CORS_ORIGINS`

Példa frontend kulcsok:
- `VITE_API_BASE_URL`
- `VITE_APP_NAME`

## 10. Induló fájlok

### Backend
- `backend/app/main.py`
- `backend/app/api/router.py`
- `backend/app/api/health.py`
- `backend/app/core/config.py`
- `backend/app/core/security.py`
- `backend/app/core/auth.py`
- `backend/app/core/logging.py`
- `backend/app/core/dependencies.py`
- `backend/app/db/base.py`
- `backend/app/db/session.py`
- `backend/app/db/models_registry.py`
- `backend/alembic.ini`
- `backend/migrations/env.py`
- `backend/pyproject.toml`
- `backend/.env.example`

### Frontend
- `frontend/src/main.tsx`
- `frontend/src/app/App.tsx`
- `frontend/src/app/providers.tsx`
- `frontend/src/routes/index.tsx`
- `frontend/src/routes/protected.tsx`
- `frontend/src/services/api/client.ts`
- `frontend/src/services/api/authClient.ts`
- `frontend/src/services/queries/queryClient.ts`
- `frontend/src/services/storage/tokenStorage.ts`
- `frontend/src/shared/constants/routes.ts`
- `frontend/src/shared/components/layout/AppLayout.tsx`
- `frontend/package.json`
- `frontend/vite.config.ts`
- `frontend/tsconfig.json`
- `frontend/.env.example`

## 11. Mi nem cél ebben a fázisban

Ebben a lépésben még nem cél:
- teljes üzleti logika implementálása
- adatbázis modellek végleges kidolgozása
- endpointok teljes implementációja
- frontend képernyők kidolgozása
- integrációk megírása

Ez a fázis kizárólag a stabil technikai alapot rögzíti.
