"""Dependency wiring for the imports presentation layer."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db_session
from app.modules.imports.application.commands.upload_import_file import (
    UploadImportFileCommand,
)
from app.modules.imports.application.commands.parse_import_batch import (
    ParseImportBatchCommand,
)
from app.modules.imports.application.queries.list_import_batches import (
    ListImportBatchesQuery,
)
from app.modules.imports.application.services.import_parser_service import (
    CsvImportParser,
)
from app.modules.imports.infrastructure.repositories.sqlalchemy_import_batch_repository import (
    SqlAlchemyImportBatchRepository,
)
from app.modules.imports.infrastructure.storage.local_import_file_storage import (
    LocalImportFileStorage,
)

DbSession = Annotated[Session, Depends(get_db_session)]


def get_upload_import_file_command(session: DbSession) -> UploadImportFileCommand:
    """Wire the upload command to its repository and storage adapter."""

    repository = SqlAlchemyImportBatchRepository(session)
    storage = LocalImportFileStorage(get_settings().imports_storage_dir)
    return UploadImportFileCommand(repository, storage)


def get_list_import_batches_query(session: DbSession) -> ListImportBatchesQuery:
    """Wire the batch list query to its repository."""

    repository = SqlAlchemyImportBatchRepository(session)
    return ListImportBatchesQuery(repository)


def get_parse_import_batch_command(session: DbSession) -> ParseImportBatchCommand:
    """Wire the parse command to its repository and parser service."""

    repository = SqlAlchemyImportBatchRepository(session)
    parser = CsvImportParser()
    return ParseImportBatchCommand(repository, parser)
