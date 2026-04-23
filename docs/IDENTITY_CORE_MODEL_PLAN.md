# BizTracker Identity and Core Master Data Model Plan

Ez a dokumentum az első `identity` és `core master data` ORM modelltervet rögzíti kontrollált mélységben. A cél nem a teljes implementáció, hanem az adatmodell és az első Alembic revisionök egyértelműsítése.

Kapcsolódó dokumentumok:
- [ARCHITECTURE.md](C:\BizTracker\docs\ARCHITECTURE.md)
- [MVP_IMPLEMENTATION_PLAN.md](C:\BizTracker\docs\MVP_IMPLEMENTATION_PLAN.md)
- [MIGRATION_PLAN.md](C:\BizTracker\docs\MIGRATION_PLAN.md)

## 1. Kiinduló feltételezések

Explicit feltételezések:
- PostgreSQL-t használunk
- SQLAlchemy 2 stílusban modellezünk
- az operatív táblák elsődleges kulcsa `UUID`
- az identity táblák az `auth` sémába kerülnek
- a master data táblák a `core` sémába kerülnek
- az enum-jellegű mezőket első körben `String` oszlopként kezeljük, nem PostgreSQL enumként
- a legtöbb modellnél lesz `created_at` és `updated_at`, de a kapcsolótábláknál ezt minimálisan kezeljük

Miért nem használunk most rögtön PostgreSQL enumot:
- csökkenti a korai migration-súrlódást,
- egyszerűbb refaktorálni a korai iterációkban,
- az értékkészlet validálható application rétegben is.

## 2. Közös modellezési szabályok

### 2.1. Általános technikai konvenciók

- PK: `UUID`
- időbélyegek: `DateTime(timezone=True)`
- pénzügyi mennyiségekhez később `Numeric`, ezek most nem érintettek mélyen
- string mezőknél célzott, nem túl laza hosszkorlátok
- kötelező idegen kulcsokra explicit index
- kapcsolótáblákhoz összetett elsődleges kulcs

### 2.2. SQLAlchemy 2 irány

Az ORM modellek tervezése ehhez igazodjon:
- `Mapped[T]`
- `mapped_column(...)`
- `relationship(...)`
- közös `Base`
- opcionálisan közös mixinek:
  - `UUIDPrimaryKeyMixin`
  - `TimestampMixin`

Ez most még tervszintű döntés, nem végleges implementáció.

## 3. Identity modul első ORM modelljei

## 3.1. `auth.user`

### Cél
Belső felhasználók tárolása és hitelesítés támogatása.

### Javasolt mezők

| Mező | Típus | Null | Megjegyzés |
|---|---|---|---|
| `id` | `UUID` | nem | PK |
| `email` | `String(320)` | nem | normalizált, lowercase formában tárolva |
| `password_hash` | `String(255)` | nem | jelszó hash |
| `full_name` | `String(200)` | nem | megjelenítési név |
| `is_active` | `Boolean` | nem | default `true` |
| `last_login_at` | `DateTime(timezone=True)` | igen | utolsó sikeres login |
| `created_at` | `DateTime(timezone=True)` | nem | default `now()` |
| `updated_at` | `DateTime(timezone=True)` | nem | default `now()` + update |

### Kulcsok
- PK: `id`

### Indexek
- egyedi index `email` mezőn

### Unique constraint
- `uq_auth_user_email`

### Fő kapcsolatok
- M:N `role` a `auth.user_role` kapcsolótáblán keresztül

### Megjegyzés
Nem vezetünk be még:
- password reset token táblát
- MFA táblákat
- business unit hozzáférési mátrixot

## 3.2. `auth.role`

### Cél
Szerepkörök tárolása authorization célra.

### Javasolt mezők

| Mező | Típus | Null | Megjegyzés |
|---|---|---|---|
| `id` | `UUID` | nem | PK |
| `code` | `String(50)` | nem | technikai azonosító, pl. `admin` |
| `name` | `String(100)` | nem | megjelenítési név |
| `description` | `String(255)` | igen | opcionális |
| `is_active` | `Boolean` | nem | default `true` |
| `created_at` | `DateTime(timezone=True)` | nem | default `now()` |
| `updated_at` | `DateTime(timezone=True)` | nem | default `now()` + update |

### Kulcsok
- PK: `id`

### Indexek
- egyedi index `code` mezőn

### Unique constraint
- `uq_auth_role_code`

### Fő kapcsolatok
- M:N `user` a `auth.user_role` táblán át
- M:N `permission` a `auth.role_permission` táblán át

## 3.3. `auth.permission`

### Cél
Finomabb jogosultsági egységek tárolása.

### Javasolt mezők

| Mező | Típus | Null | Megjegyzés |
|---|---|---|---|
| `id` | `UUID` | nem | PK |
| `code` | `String(100)` | nem | pl. `inventory.read` |
| `name` | `String(150)` | nem | megjelenítési név |
| `description` | `String(255)` | igen | opcionális |
| `created_at` | `DateTime(timezone=True)` | nem | default `now()` |
| `updated_at` | `DateTime(timezone=True)` | nem | default `now()` + update |

### Kulcsok
- PK: `id`

### Indexek
- egyedi index `code` mezőn

### Unique constraint
- `uq_auth_permission_code`

### Fő kapcsolatok
- M:N `role` a `auth.role_permission` táblán át

## 3.4. `auth.user_role`

### Cél
Felhasználó és szerepkör kapcsolata.

### Javasolt mezők

| Mező | Típus | Null | Megjegyzés |
|---|---|---|---|
| `user_id` | `UUID` | nem | FK `auth.user.id` |
| `role_id` | `UUID` | nem | FK `auth.role.id` |
| `assigned_at` | `DateTime(timezone=True)` | nem | default `now()` |

### Kulcsok
- összetett PK: (`user_id`, `role_id`)

### Indexek
- index `role_id` mezőn

### Unique constraint
- külön nem szükséges, az összetett PK ezt lefedi

### Fő kapcsolatok
- N:1 `user`
- N:1 `role`

### FK viselkedés
- `user_id` `ON DELETE CASCADE`
- `role_id` `ON DELETE CASCADE`

## 3.5. `auth.role_permission`

### Cél
Szerepkör és jogosultság kapcsolata.

### Javasolt mezők

| Mező | Típus | Null | Megjegyzés |
|---|---|---|---|
| `role_id` | `UUID` | nem | FK `auth.role.id` |
| `permission_id` | `UUID` | nem | FK `auth.permission.id` |
| `assigned_at` | `DateTime(timezone=True)` | nem | default `now()` |

### Kulcsok
- összetett PK: (`role_id`, `permission_id`)

### Indexek
- index `permission_id` mezőn

### Unique constraint
- külön nem szükséges, az összetett PK ezt lefedi

### Fő kapcsolatok
- N:1 `role`
- N:1 `permission`

### FK viselkedés
- `role_id` `ON DELETE CASCADE`
- `permission_id` `ON DELETE CASCADE`

## 4. Core master data első ORM modelljei

## 4.1. `core.business_unit`

### Cél
Az üzleti egységek központi törzsadata.

### Javasolt mezők

| Mező | Típus | Null | Megjegyzés |
|---|---|---|---|
| `id` | `UUID` | nem | PK |
| `code` | `String(50)` | nem | technikai azonosító, pl. `gourmand`, `flow` |
| `name` | `String(150)` | nem | üzleti név |
| `type` | `String(50)` | nem | pl. `bakery`, `music_club` |
| `is_active` | `Boolean` | nem | default `true` |
| `created_at` | `DateTime(timezone=True)` | nem | default `now()` |
| `updated_at` | `DateTime(timezone=True)` | nem | default `now()` + update |

### Kulcsok
- PK: `id`

### Indexek
- egyedi index `code` mezőn

### Unique constraint
- `uq_core_business_unit_code`

### Fő kapcsolatok
- 1:N `location`
- 1:N `category`
- 1:N `product`
- később 1:N `inventory_item`, `supplier`, `financial_transaction`

## 4.2. `core.location`

### Cél
Fizikai üzlet, telephely vagy venue reprezentációja.

### Javasolt mezők

| Mező | Típus | Null | Megjegyzés |
|---|---|---|---|
| `id` | `UUID` | nem | PK |
| `business_unit_id` | `UUID` | nem | FK `core.business_unit.id` |
| `name` | `String(150)` | nem | megjelenítési név |
| `kind` | `String(50)` | nem | pl. `store`, `venue`, `warehouse_site` |
| `is_active` | `Boolean` | nem | default `true` |
| `created_at` | `DateTime(timezone=True)` | nem | default `now()` |
| `updated_at` | `DateTime(timezone=True)` | nem | default `now()` + update |

### Kulcsok
- PK: `id`
- FK: `business_unit_id -> core.business_unit.id`

### Indexek
- index `business_unit_id`

### Unique constraint
- `uq_core_location_business_unit_name` a (`business_unit_id`, `name`) mezőkön

### Fő kapcsolatok
- N:1 `business_unit`
- később 1:N `warehouse`
- később 1:N `financial_transaction`
- később 1:N `event`

### FK viselkedés
- `business_unit_id` `ON DELETE RESTRICT`

## 4.3. `core.unit_of_measure`

### Cél
Mértékegységek közös törzsadata.

### Javasolt mezők

| Mező | Típus | Null | Megjegyzés |
|---|---|---|---|
| `id` | `UUID` | nem | PK |
| `code` | `String(20)` | nem | pl. `kg`, `pcs`, `l` |
| `name` | `String(100)` | nem | teljes név |
| `symbol` | `String(20)` | igen | opcionális rövidítés |
| `created_at` | `DateTime(timezone=True)` | nem | default `now()` |
| `updated_at` | `DateTime(timezone=True)` | nem | default `now()` + update |

### Kulcsok
- PK: `id`

### Indexek
- egyedi index `code` mezőn

### Unique constraint
- `uq_core_unit_of_measure_code`

### Fő kapcsolatok
- később 1:N `inventory_item`
- később 1:N recept- és gyártási mezők

## 4.4. `core.category`

### Cél
Üzleti egységen belüli termék- vagy elemkategóriák kezelése.

### Javasolt mezők

| Mező | Típus | Null | Megjegyzés |
|---|---|---|---|
| `id` | `UUID` | nem | PK |
| `business_unit_id` | `UUID` | nem | FK `core.business_unit.id` |
| `parent_id` | `UUID` | igen | önhivatkozó FK `core.category.id` |
| `name` | `String(150)` | nem | kategórianév |
| `is_active` | `Boolean` | nem | default `true` |
| `created_at` | `DateTime(timezone=True)` | nem | default `now()` |
| `updated_at` | `DateTime(timezone=True)` | nem | default `now()` + update |

### Kulcsok
- PK: `id`
- FK: `business_unit_id -> core.business_unit.id`
- FK: `parent_id -> core.category.id`

### Indexek
- index `business_unit_id`
- index `parent_id`
- nem egyedi összetett index (`business_unit_id`, `parent_id`, `name`) a gyorsabb lookuphoz

### Unique constraint
- első körben nincs külön unique constraint

### Fő kapcsolatok
- N:1 `business_unit`
- N:1 `parent`
- 1:N `children`
- 1:N `product`

### FK viselkedés
- `business_unit_id` `ON DELETE RESTRICT`
- `parent_id` `ON DELETE SET NULL`

## 4.5. `core.product`

### Cél
Eladható vagy üzletileg nyilvántartott termékek elsődleges törzsadata.

### Javasolt mezők

| Mező | Típus | Null | Megjegyzés |
|---|---|---|---|
| `id` | `UUID` | nem | PK |
| `business_unit_id` | `UUID` | nem | FK `core.business_unit.id` |
| `category_id` | `UUID` | igen | FK `core.category.id` |
| `sku` | `String(64)` | igen | külső vagy belső cikkszám, még nem kötelező |
| `name` | `String(200)` | nem | terméknév |
| `product_type` | `String(50)` | nem | pl. `finished_product`, `drink`, `ticketed_item` |
| `is_active` | `Boolean` | nem | default `true` |
| `created_at` | `DateTime(timezone=True)` | nem | default `now()` |
| `updated_at` | `DateTime(timezone=True)` | nem | default `now()` + update |

### Kulcsok
- PK: `id`
- FK: `business_unit_id -> core.business_unit.id`
- FK: `category_id -> core.category.id`

### Indexek
- index `business_unit_id`
- index `category_id`
- nem egyedi index `sku`
- nem egyedi összetett index (`business_unit_id`, `name`)

### Unique constraint
- első körben nincs külön unique constraint

### Fő kapcsolatok
- N:1 `business_unit`
- N:1 `category`
- később 1:N `recipe`

### FK viselkedés
- `business_unit_id` `ON DELETE RESTRICT`
- `category_id` `ON DELETE SET NULL`

## 5. Összefoglaló: mely constraint-eket vezetjük be most

### Most bevezetendő, stabil constraint-ek

- minden PK
- minden alap FK
- `auth.user.email` unique
- `auth.role.code` unique
- `auth.permission.code` unique
- `core.business_unit.code` unique
- `core.unit_of_measure.code` unique
- `core.location (business_unit_id, name)` unique
- kapcsolótáblák összetett PK-ja

### Miért ezeket most

Ezek:
- technikailag stabilak,
- kevés üzleti bizonytalanságot hordoznak,
- az adattisztaságot erősen javítják,
- később valószínűleg nem kell őket visszavenni.

## 6. Mely constraint-eket érdemes későbbre hagyni

### `core.category` egyediség

Most még ne vezessünk be például ilyet:
- (`business_unit_id`, `parent_id`, `name`) unique

Miért később:
- a kategóriafa szerkezete még változhat,
- a `NULL` parent kezelésnél külön figyelmet igényelne,
- előbb célszerű validálni a valós törzsadatokat.

### `core.product.sku` egyediség

Most még ne vezessünk be:
- (`business_unit_id`, `sku`) unique

Miért később:
- a külső exportokban a SKU minősége bizonytalan lehet,
- előfordulhat hiányos vagy nem konzisztens adat,
- az MVP-t nem szabad megtörni emiatt.

### `role.name`, `permission.name`, `business_unit.name` egyediség

Most ne legyen unique:
- megjelenítési név változhat,
- technikai azonosítónak a `code` elég.

### Check constraint-ek enum jellegű mezőkre

Példák:
- `business_unit.type`
- `location.kind`
- `product.product_type`

Most ne vezessük be DB-szinten.

Miért később:
- a korai iterációban gyorsabban változhat az értékkészlet,
- application oldali validáció most rugalmasabb.

## 7. Első Alembic revision backlog

Javasolt sorrend:

1. `001_create_schemas`
2. `002_auth_identity_base`
3. `003_core_master_data_foundation`
4. `004_core_category_product_base`

## 7.1. `001_create_schemas`

### Tartalom
- `auth` séma létrehozása
- `core` séma létrehozása
- későbbi kompatibilitás miatt opcionálisan `ingest` és `analytics` séma is létrehozható ugyanitt

### Függőség
- nincs

## 7.2. `002_auth_identity_base`

### Tartalom
- `auth.user`
- `auth.role`
- `auth.permission`
- `auth.user_role`
- `auth.role_permission`

### Függőség
- `001_create_schemas`

### Miért egy revision
- szorosan összetartozó identity alap
- együtt alkotnak működő auth minimumot
- külön bontás itt még nem ad valódi előnyt

## 7.3. `003_core_master_data_foundation`

### Tartalom
- `core.business_unit`
- `core.location`
- `core.unit_of_measure`

### Függőség
- technikailag `001_create_schemas`
- rollout szempontból érdemes `002_auth_identity_base` után futtatni

### Miért egy revision
- ez a minimum master data foundation
- a location közvetlenül business unitra épül
- a unit of measure ugyan független, de ugyanabba a hullámba jól illik

## 7.4. `004_core_category_product_base`

### Tartalom
- `core.category`
- `core.product`

### Függőség
- `003_core_master_data_foundation`

### Miért külön revision
- a kategória és product réteg már üzletileg képlékenyebb
- ha a taxonómia változik, ezt jobb külön revisionben tartani
- a master data alap ettől függetlenül is használható marad

## 8. Revisionök közti fő függőségek

### Identity
- nincs függése a core master datára

### Business unit és location
- `location` csak `business_unit` után hozható létre

### Category
- `category` függ a `business_unit` táblától
- az önhivatkozó FK miatt ugyanabban a táblában kezelhető

### Product
- `product` függ a `business_unit` és `category` tábláktól
- ezért kerüljön a categoryvel azonos vagy utána következő revisionbe

## 9. Javasolt seed backlog az első revisionök után

Első seedelendő rekordok:
- role: `admin`, `manager`, `analyst`
- business unit: `gourmand`, `flow`
- unit of measure: `pcs`, `kg`, `g`, `l`, `ml`

Nem érdemes migrationbe égetni első körben:
- category teljes fa
- product lista
- felhasználók

Ezek vagy admin felületről, vagy külön bootstrap scriptből kerüljenek be.

## 10. Mi maradjon későbbi modellkörre

Ne kerüljön most bele:
- `user_business_unit` vagy finomabb hozzáférési mátrix
- audit trail táblák
- soft delete összetett stratégia
- slug mezők
- lokalizációs mezők
- kategóriafa mélység- vagy path-optimalizáció
- product variant vagy product bundle logika

Ezeket csak akkor érdemes behozni, ha a valós használat indokolja.

## 11. Rövid implementációs irány ORM szinten

Az első implementációs körben az ORM modellek fájljai várhatóan:
- `backend/app/modules/identity/infrastructure/orm/user_model.py`
- `backend/app/modules/identity/infrastructure/orm/role_model.py`
- `backend/app/modules/identity/infrastructure/orm/permission_model.py`
- `backend/app/modules/identity/infrastructure/orm/user_role_model.py`
- `backend/app/modules/identity/infrastructure/orm/role_permission_model.py`
- `backend/app/modules/master_data` jelenleg nincs külön modulnéven scaffoldolva, ezért ideiglenesen a `core` törzsadat-modellek helyét még véglegesíteni kell

Ajánlott technikai irány:
- a `core master data` számára később külön `master_data` modul létrehozása
- addig ne keverjük szét a modelleket más domain modulok közé

Megjegyzés:
- a jelenlegi scaffoldban külön `master_data` modul még nincs létrehozva, mert az előző terv a domain modulokra fókuszált
- a következő technikai körben ezt érdemes külön, tisztán bevezetni

