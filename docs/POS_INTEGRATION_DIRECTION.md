# POS Integration Direction

Ez a dokumentum azt rogziti, hogy a Demo POS nem a kesobbi hivatalos kassza helyettesitoje, hanem csak tesztkliens az adatfolyam vizsgalatahoz.

## Alapelv

A kasszaprogram kulso, hivatalos rendszer. A BizTracker nem epulhet ugy, mintha a demo kassza lenne a vegleges kassza. A BizTracker feladata egy tiszta ingestion boundary fenntartasa, amelyhez kesobb egy kulso connector vagy adapter illeszti a valodi kasszabol erkezo adatot.

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

## Demo POS szerepe

Frontend oldal:

```text
/demo-pos
```

Demo API:

```text
GET /api/v1/demo-pos/catalog
POST /api/v1/demo-pos/receipts
```

A demo frontend nyugtakuldesnel mar a `pos-ingestion` endpointot hasznalja. A `demo-pos` modul celja tovabbra is a tesztkatalogus es a fejlesztoi demo flow tamogatasa.

## Kesobbi valodi kassza adapter

A valodi kassza integracional nem a dashboardot, finance modult vagy import reteg belsejet kell atirni, hanem egy adaptert kell epiteni, amely:
- a hivatalos kassza API-jabol vagy exportjabol olvas
- a kulso termekkodokat BizTracker `product_id` / `sku` ertekekre mappeli
- a fizetesi modot, timestampet es mennyiseget normalizalja
- ugyanarra a `POST /api/v1/pos-ingestion/receipts` szerzodesre kuld

## Nyitott adatok

A valodi integracio elott tisztazando:
- kasszaprogram pontos API/export formatuma
- termekkod, vonalkod vagy PLU megfeleltetes
- mennyisegi modell: db, kg, adag, gomboc
- sztorno, visszaru, kedvezmeny es borravalo kezelese
- napzartas es offline ujrakuldes szabalyai
