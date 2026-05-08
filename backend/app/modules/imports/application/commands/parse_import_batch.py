"""Parse one uploaded import batch into staging rows."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.modules.imports.application.services.import_parser_service import CsvImportParser
from app.modules.imports.domain.entities.import_batch import (
    ImportBatch,
    NewImportRowError,
)
from app.modules.imports.domain.repositories.import_batch_repository import (
    ImportBatchRepository,
)
from app.modules.pos_ingestion.application.services.pos_sale_catalog_sync import (
    PosSaleCatalogSyncService,
)


class ImportBatchNotFoundError(Exception):
    """Raised when a batch id does not exist."""


class ImportBatchStateError(Exception):
    """Raised when a batch cannot be parsed in its current state."""


@dataclass(frozen=True, slots=True)
class ParseImportBatchSummary:
    """Returned to aid later testing or logging if needed."""

    total_rows: int
    parsed_rows: int
    error_rows: int


class ParseImportBatchCommand:
    """Parse one uploaded batch and persist staging metadata."""

    def __init__(
        self,
        repository: ImportBatchRepository,
        parser: CsvImportParser,
        catalog_sync: PosSaleCatalogSyncService | None = None,
    ) -> None:
        self._repository = repository
        self._parser = parser
        self._catalog_sync = catalog_sync

    def execute(self, *, batch_id: uuid.UUID) -> ImportBatch:
        batch = self._repository.get_batch(batch_id)
        if batch is None:
            raise ImportBatchNotFoundError(f"Import batch {batch_id} was not found.")

        if batch.status != "uploaded":
            raise ImportBatchStateError(
                f"Only uploaded batches can be parsed. Current status: {batch.status}."
            )

        if not batch.files:
            raise ImportBatchStateError("The import batch does not contain any files.")

        self._repository.mark_parsing(batch_id)

        rows = []
        errors = []
        total_rows = 0
        parsed_rows = 0
        error_rows = 0

        try:
            batch_result = self._parser.parse_batch(
                files=batch.files,
                import_type=batch.import_type,
            )
            if batch_result is not None:
                total_rows = batch_result.total_rows
                parsed_rows = batch_result.parsed_rows
                error_rows = batch_result.error_rows
                self._sync_catalog(
                    batch_id=batch_id,
                    business_unit_id=batch.business_unit_id,
                    source_system=batch.import_type,
                    rows=list(batch_result.rows),
                )
                return self._repository.finalize_parsed(
                    batch_id=batch_id,
                    rows=list(batch_result.rows),
                    errors=list(batch_result.errors),
                    total_rows=batch_result.total_rows,
                    parsed_rows=batch_result.parsed_rows,
                    error_rows=batch_result.error_rows,
                )

            for import_file in batch.files:
                result = self._parser.parse(
                    file_id=import_file.id,
                    file_path=import_file.stored_path,
                    import_type=batch.import_type,
                )
                rows.extend(result.rows)
                errors.extend(result.errors)
                total_rows += result.total_rows
                parsed_rows += result.parsed_rows
                error_rows += result.error_rows

            self._sync_catalog(
                batch_id=batch_id,
                business_unit_id=batch.business_unit_id,
                source_system=batch.import_type,
                rows=rows,
            )
            return self._repository.finalize_parsed(
                batch_id=batch_id,
                rows=rows,
                errors=errors,
                total_rows=total_rows,
                parsed_rows=parsed_rows,
                error_rows=error_rows,
            )
        except Exception as exc:
            fallback_error = NewImportRowError(
                file_id=batch.files[0].id,
                row_number=None,
                field_name=None,
                error_code="unexpected_parse_error",
                message=str(exc),
                raw_payload=None,
            )
            self._repository.rollback()
            return self._repository.mark_failed(
                batch_id=batch_id,
                errors=[fallback_error],
                total_rows=total_rows,
                parsed_rows=parsed_rows,
                error_rows=max(error_rows, 1),
            )

    def _sync_catalog(
        self,
        *,
        batch_id: uuid.UUID,
        business_unit_id: uuid.UUID,
        source_system: str,
        rows,
    ) -> None:
        if self._catalog_sync is None:
            return
        self._catalog_sync.sync_new_rows(
            business_unit_id=business_unit_id,
            rows=rows,
            source_system=source_system,
            batch_id=batch_id,
        )
