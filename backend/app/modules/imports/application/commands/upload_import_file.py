"""Upload import file use case."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from fastapi import UploadFile

from app.modules.imports.domain.entities.import_batch import ImportBatch, NewImportFile
from app.modules.imports.domain.repositories.import_batch_repository import (
    ImportBatchRepository,
)


@dataclass(frozen=True, slots=True)
class StoredImportFile:
    """Metadata returned after persisting a physical upload."""

    original_name: str
    stored_path: str
    mime_type: str | None
    size_bytes: int


class ImportFileStorage(Protocol):
    """Stores uploaded files and returns their metadata."""

    def store(self, upload: UploadFile) -> StoredImportFile:
        """Persist the uploaded file."""


class UploadImportFileCommand:
    """Create an import batch and persist the uploaded file metadata."""

    def __init__(
        self,
        repository: ImportBatchRepository,
        storage: ImportFileStorage,
    ) -> None:
        self._repository = repository
        self._storage = storage

    def execute(
        self,
        *,
        business_unit_id: uuid.UUID,
        import_type: str,
        upload: UploadFile,
    ) -> ImportBatch:
        stored_file = self._storage.store(upload)
        return self._repository.create_uploaded_batch(
            business_unit_id=business_unit_id,
            import_type=import_type,
            original_name=stored_file.original_name,
            stored_path=stored_file.stored_path,
            mime_type=stored_file.mime_type,
            size_bytes=stored_file.size_bytes,
        )

    def execute_many(
        self,
        *,
        business_unit_id: uuid.UUID,
        import_type: str,
        uploads: Sequence[UploadFile],
    ) -> ImportBatch:
        stored_files = [self._storage.store(upload) for upload in uploads]
        return self._repository.create_uploaded_batch_with_files(
            business_unit_id=business_unit_id,
            import_type=import_type,
            files=[
                NewImportFile(
                    original_name=file.original_name,
                    stored_path=file.stored_path,
                    mime_type=file.mime_type,
                    size_bytes=file.size_bytes,
                )
                for file in stored_files
            ],
        )
