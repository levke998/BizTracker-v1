"""Safely recover a stuck POS import batch.

The script only resets a batch when it has no persisted staging rows and no
mapped finance transactions. This keeps recovery idempotent for parse failures
that happened before data was committed.
"""

from __future__ import annotations

import argparse
import json
from typing import Any
from uuid import UUID

from sqlalchemy import text

from app.db.session import SessionLocal
from app.modules.finance.application.commands.map_pos_sales_batch_to_transactions import (
    MapPosSalesBatchToTransactionsCommand,
)
from app.modules.finance.infrastructure.repositories.sqlalchemy_transaction_repository import (
    SqlAlchemyFinancialTransactionRepository,
)
from app.modules.imports.application.commands.parse_import_batch import (
    ParseImportBatchCommand,
)
from app.modules.imports.application.services.import_parser_service import CsvImportParser
from app.modules.imports.infrastructure.repositories.sqlalchemy_import_batch_repository import (
    SqlAlchemyImportBatchRepository,
)
from app.modules.pos_ingestion.application.services.pos_sale_catalog_sync import (
    PosSaleCatalogSyncService,
)
from app.modules.pos_ingestion.application.services.pos_sale_inventory import (
    PosSaleInventoryConsumptionService,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-id", required=True, type=UUID)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--map-finance", action="store_true")
    args = parser.parse_args()

    session = SessionLocal()
    try:
        before = _inspect_batch(session, args.batch_id)
        print("BEFORE", _json(before))
        _assert_recoverable(before)

        if not args.apply:
            print("DRY_RUN recoverable=true")
            return

        session.execute(
            text(
                """
                update ingest.import_batch
                set status = 'uploaded',
                    finished_at = null,
                    total_rows = 0,
                    parsed_rows = 0,
                    error_rows = 0
                where id = :batch_id
                """
            ),
            {"batch_id": args.batch_id},
        )
        session.commit()

        imports_repository = SqlAlchemyImportBatchRepository(session)
        parsed = ParseImportBatchCommand(
            imports_repository,
            CsvImportParser(),
            catalog_sync=PosSaleCatalogSyncService(session),
        ).execute(batch_id=args.batch_id)
        print(
            "PARSED",
            _json(
                {
                    "status": parsed.status,
                    "total_rows": parsed.total_rows,
                    "parsed_rows": parsed.parsed_rows,
                    "error_rows": parsed.error_rows,
                    "first_occurred_at": parsed.first_occurred_at,
                    "last_occurred_at": parsed.last_occurred_at,
                }
            ),
        )

        if args.map_finance:
            mapped = MapPosSalesBatchToTransactionsCommand(
                imports_repository=imports_repository,
                finance_repository=SqlAlchemyFinancialTransactionRepository(session),
                inventory_consumption=PosSaleInventoryConsumptionService(session),
            ).execute(batch_id=args.batch_id)
            print(
                "MAPPED",
                _json({"created_transactions": mapped.created_transactions}),
            )

        after = _inspect_batch(session, args.batch_id)
        print("AFTER", _json(after))
        print("DUPLICATE_DEDUPE_KEYS", _json(_duplicate_dedupe_keys(session)))
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _assert_recoverable(batch: dict[str, Any]) -> None:
    if batch["status"] not in {"parsing", "failed"}:
        raise SystemExit(f"Batch is not stuck or failed: {batch['status']}")
    if batch["row_count"] != 0:
        raise SystemExit(f"Batch already has staging rows: {batch['row_count']}")
    if batch["tx_count"] != 0:
        raise SystemExit(f"Batch already has finance transactions: {batch['tx_count']}")


def _inspect_batch(session, batch_id: UUID) -> dict[str, Any]:
    row = session.execute(
        text(
            """
            select
                b.id,
                b.status,
                b.total_rows,
                b.parsed_rows,
                b.error_rows,
                count(distinct r.id) as row_count,
                count(distinct e.id) as err_count,
                count(distinct t.id) as tx_count
            from ingest.import_batch b
            left join ingest.import_row r on r.batch_id = b.id
            left join ingest.import_row_error e on e.batch_id = b.id
            left join core.financial_transaction t
                on t.source_type = 'import_row'
                and t.source_id = r.id
            where b.id = :batch_id
            group by b.id, b.status, b.total_rows, b.parsed_rows, b.error_rows
            """
        ),
        {"batch_id": batch_id},
    ).mappings().one_or_none()
    if row is None:
        raise SystemExit(f"Import batch was not found: {batch_id}")
    return dict(row)


def _duplicate_dedupe_keys(session) -> list[dict[str, Any]]:
    rows = session.execute(
        text(
            """
            select dedupe_key, count(*) as count
            from core.financial_transaction
            where dedupe_key is not null
            group by dedupe_key
            having count(*) > 1
            limit 10
            """
        )
    ).mappings().all()
    return [dict(row) for row in rows]


def _json(value: Any) -> str:
    return json.dumps(value, default=str, ensure_ascii=True, sort_keys=True)


if __name__ == "__main__":
    main()
