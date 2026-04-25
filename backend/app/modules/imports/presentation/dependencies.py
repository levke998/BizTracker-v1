"""Dependency wiring for the imports presentation layer."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db_session
from app.modules.finance.application.commands.map_pos_sales_batch_to_transactions import (
    MapPosSalesBatchToTransactionsCommand,
)
from app.modules.finance.infrastructure.repositories.sqlalchemy_transaction_repository import (
    SqlAlchemyFinancialTransactionRepository,
)
from app.modules.imports.application.commands.upload_import_file import (
    UploadImportFileCommand,
)
from app.modules.imports.application.commands.parse_import_batch import (
    ParseImportBatchCommand,
)
from app.modules.imports.application.queries.list_import_batches import (
    ListImportBatchesQuery,
)
from app.modules.imports.application.queries.list_import_errors import (
    ListImportErrorsQuery,
)
from app.modules.imports.application.queries.list_import_rows import (
    ListImportRowsQuery,
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
from app.modules.pos_ingestion.application.services.pos_sale_inventory import (
    PosSaleInventoryConsumptionService,
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


def get_list_import_rows_query(session: DbSession) -> ListImportRowsQuery:
    """Wire the staging rows query to its repository."""

    repository = SqlAlchemyImportBatchRepository(session)
    return ListImportRowsQuery(repository)


def get_list_import_errors_query(session: DbSession) -> ListImportErrorsQuery:
    """Wire the parse errors query to its repository."""

    repository = SqlAlchemyImportBatchRepository(session)
    return ListImportErrorsQuery(repository)


def get_parse_import_batch_command(session: DbSession) -> ParseImportBatchCommand:
    """Wire the parse command to its repository and parser service."""

    repository = SqlAlchemyImportBatchRepository(session)
    parser = CsvImportParser()
    return ParseImportBatchCommand(repository, parser)


def get_map_pos_sales_batch_to_transactions_command(
    session: DbSession,
) -> MapPosSalesBatchToTransactionsCommand:
    """Wire the import-to-finance mapping command."""

    imports_repository = SqlAlchemyImportBatchRepository(session)
    finance_repository = SqlAlchemyFinancialTransactionRepository(session)
    return MapPosSalesBatchToTransactionsCommand(
        imports_repository=imports_repository,
        finance_repository=finance_repository,
        inventory_consumption=PosSaleInventoryConsumptionService(session),
    )
