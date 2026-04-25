# POS Integration Direction

Ez a dokumentum azt rogziti, hogy a Demo POS nem a kesobbi hivatalos kassza helyettesitoje, hanem csak tesztkliens az adatfolyam vizsgalatahoz.

## Alapelv

A kasszaprogram kulso, hivatalos rendszer. A BizTracker nem epulhet ugy, mintha a demo kassza lenne a vegleges kassza. A BizTracker feladata egy tiszta ingestion boundary fenntartasa, amelyhez kesobb egy kulso connector vagy adapter illeszti a valodi kasszabol erkezo adatot.

Ha nincs meg a kasszakapcsolat, vagy atmenetileg kiesik, a rendszer tovabbra is mukodokepes marad. Ilyenkor az eladasi adatok CSV exportbol erkeznek az import kozponton keresztul.

## Jelenlegi szerzodes

Normalized receipt endpoint:

```text
POST /api/v1/pos-ingestion/receipts
```

Ez fogad:
- business unit
- payment method
- receipt number
- occurred_at timestamp
- product_id + quantity sorok

A backend ezutan:
- `ingest.import_batch` rekordot hoz letre
- `ingest.import_file` demo/API forrast rogziti
- `ingest.import_row` sorokat hoz letre normalized payload-dal
- `core.financial_transaction` `pos_sale` inflow rekordokat keszit

## CSV fallback

A kassza CSV exportja a meglévo import flow-val toltheto fel:

```text
POST /api/v1/imports/files
POST /api/v1/imports/batches/{batch_id}/parse
POST /api/v1/imports/batches/{batch_id}/map/financial-transactions
```

Import type:

```text
pos_sales
```

Minimalis oszlopok:
- `date`
- `receipt_no`
- `product_name`
- `quantity`
- `gross_amount`
- `payment_method`

Opcionális, kesobbi kassza API/export eseten hasznos oszlopok:
- `sku`
- `product_id`
- `category_name`

## Duplikacio vedelem

A POS sale sorok stabil dedupe kulcsot kapnak. A kulcs forrastol fuggetlenul ugyanugy epul:
- business unit
- date
- receipt number
- product name
- quantity
- gross amount

Ez azt jelenti, hogy:
- ugyanaz a CSV egymas utan feltoltve nem hoz letre dupla penzugyi tranzakciot
- ha API-n mar megerkezett az eladas, a kesobbi CSV fallback nem duplazza
- ha CSV-bol mar bekerult az eladas, a kesobbi API kuldes nem duplazza
- a becsult stock fogyas is csak az elfogadott, nem duplikalt sorokra fut

Technikai alap:
- `core.financial_transaction.dedupe_key`
- egyedi index: `ix_core_financial_transaction_dedupe_key`

## Demo POS szerepe

Frontend oldal:

```text
/demo-pos
```

Demo API:

```text
GET /api/v1/demo-pos/catalog
GET /api/v1/demo-pos/receipts
POST /api/v1/demo-pos/receipts
```

A demo frontend nyugtakuldesnel mar a `pos-ingestion` endpointot hasznalja. A `demo-pos` modul celja tovabbra is a tesztkatalogus es a fejlesztoi demo flow tamogatasa.

Az utolso demo nyugtak listaja perzisztalt `ingest.import_row` es `core.financial_transaction` sorokbol epul vissza. Ez tudatosan ugyanazt az igazsagot mutatja, amelybol a dashboard es a finance read model is dolgozik; a demo kassza sajat lokalis runtime listaja nem tekintheto adatforrasnak.

## Kesobbi valodi kassza adapter

A valodi kassza integracional nem a dashboardot, finance modult vagy import reteg belsejet kell atirni, hanem egy adaptert kell epiteni, amely:
- a hivatalos kassza API-jabol vagy exportjabol olvas
- a kulso termekkodokat BizTracker `product_id` / `sku` ertekekre mappeli
- a fizetesi modot, timestampet es mennyiseget normalizalja
- ugyanarra a `POST /api/v1/pos-ingestion/receipts` szerzodesre kuld

Amig a kulso kasszakod nem ismert, a rendszer `product_name` es kesobb `sku` alapon is tud dolgozni. A kasszakod mapping felulet kulon kovetkezo szelet lesz, amikor megkapjuk a valodi API/export specifikaciot.

## Nyitott adatok

A valodi integracio elott tisztazando:
- kasszaprogram pontos API/export formatuma
- termekkod, vonalkod vagy PLU megfeleltetes
- mennyisegi modell: db, kg, adag, gomboc
- sztorno, visszaru, kedvezmeny es borravalo kezelese
- napzartas es offline ujrakuldes szabalyai
