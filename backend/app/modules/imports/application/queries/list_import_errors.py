"""List parse errors for one import batch."""

from __future__ import annotations

import uuid

from app.modules.imports.domain.entities.import_batch import ImportRowError
from app.modules.imports.domain.repositories.import_batch_repository import (
    ImportBatchRepository,
)


class ImportBatchErrorsNotFoundError(Exception):
    """Raised when the requested import batch does not exist."""


class ListImportErrorsQuery:
    """Read-only use case for parse errors of one batch."""

    def __init__(self, repository: ImportBatchRepository) -> None:
        self._repository = repository

    def execute(self, *, batch_id: uuid.UUID, limit: int = 20) -> list[ImportRowError]:
        batch = self._repository.get_batch(batch_id)
        if batch is None:
            raise ImportBatchErrorsNotFoundError(
                f"Import batch {batch_id} was not found."
            )

        return self._repository.list_errors(batch_id=batch_id, limit=limit)
