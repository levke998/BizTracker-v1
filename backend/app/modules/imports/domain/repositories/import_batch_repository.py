"""Import batch repository contract."""

from __future__ import annotations

import uuid
from typing import Protocol

from app.modules.imports.domain.entities.import_batch import (
    ImportBatch,
    ImportRow,
    ImportRowError,
    NewImportRow,
    NewImportRowError,
)


class ImportBatchRepository(Protocol):
    """Defines persistence operations needed by the MVP import flow."""

    def create_uploaded_batch(
        self,
        *,
        business_unit_id: uuid.UUID,
        import_type: str,
        original_name: str,
        stored_path: str,
        mime_type: str | None,
        size_bytes: int,
    ) -> ImportBatch:
        """Create a batch plus its initial uploaded file metadata."""

    def list_batches(
        self,
        *,
        business_unit_id: uuid.UUID | None = None,
    ) -> list[ImportBatch]:
        """List import batches ordered by most recent first."""

    def get_batch(self, batch_id: uuid.UUID) -> ImportBatch | None:
        """Return one import batch with its file metadata."""

    def list_rows(
        self,
        *,
        batch_id: uuid.UUID,
        limit: int = 20,
    ) -> list[ImportRow]:
        """Return the first staging rows for one batch."""

    def list_errors(
        self,
        *,
        batch_id: uuid.UUID,
        limit: int = 20,
    ) -> list[ImportRowError]:
        """Return the first parse errors for one batch."""

    def mark_parsing(self, batch_id: uuid.UUID) -> ImportBatch:
        """Move a batch to parsing status and reset parse counters."""

    def finalize_parsed(
        self,
        *,
        batch_id: uuid.UUID,
        rows: list[NewImportRow],
        errors: list[NewImportRowError],
        total_rows: int,
        parsed_rows: int,
        error_rows: int,
    ) -> ImportBatch:
        """Persist parsed staging data and finish the batch as parsed."""

    def mark_failed(
        self,
        *,
        batch_id: uuid.UUID,
        errors: list[NewImportRowError],
        total_rows: int,
        parsed_rows: int,
        error_rows: int,
    ) -> ImportBatch:
        """Mark a batch as failed and persist technical parse errors."""
