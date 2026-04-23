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
    ) -> None:
        self._repository = repository
        self._parser = parser

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
            for import_file in batch.files:
                result = self._parser.parse(
                    file_id=import_file.id,
                    file_path=import_file.stored_path,
                )
                rows.extend(result.rows)
                errors.extend(result.errors)
                total_rows += result.total_rows
                parsed_rows += result.parsed_rows
                error_rows += result.error_rows

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
            return self._repository.mark_failed(
                batch_id=batch_id,
                errors=[fallback_error],
                total_rows=total_rows,
                parsed_rows=parsed_rows,
                error_rows=max(error_rows, 1),
            )
