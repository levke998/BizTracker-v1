"""List import batches query use case."""

from __future__ import annotations

import uuid

from app.modules.imports.domain.entities.import_batch import ImportBatch
from app.modules.imports.domain.repositories.import_batch_repository import (
    ImportBatchRepository,
)


class ListImportBatchesQuery:
    """Read-only use case for listing import batches."""

    def __init__(self, repository: ImportBatchRepository) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        business_unit_id: uuid.UUID | None = None,
    ) -> list[ImportBatch]:
        return self._repository.list_batches(business_unit_id=business_unit_id)
