"""Import upload and batch listing routes."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from fastapi import HTTPException

from app.modules.imports.application.commands.parse_import_batch import (
    ImportBatchNotFoundError,
    ImportBatchStateError,
    ParseImportBatchCommand,
)
from app.modules.imports.application.commands.upload_import_file import (
    UploadImportFileCommand,
)
from app.modules.imports.application.queries.list_import_batches import (
    ListImportBatchesQuery,
)
from app.modules.imports.application.queries.list_import_errors import (
    ImportBatchErrorsNotFoundError,
    ListImportErrorsQuery,
)
from app.modules.imports.application.queries.list_import_rows import (
    ImportBatchRowsNotFoundError,
    ListImportRowsQuery,
)
from app.modules.imports.presentation.dependencies import (
    get_list_import_batches_query,
    get_list_import_errors_query,
    get_list_import_rows_query,
    get_parse_import_batch_command,
    get_upload_import_file_command,
)
from app.modules.imports.presentation.schemas.import_batch import (
    ImportBatchResponse,
    ImportRowErrorResponse,
    ImportRowResponse,
)

router = APIRouter(prefix="/imports", tags=["imports"])


@router.post(
    "/files",
    response_model=ImportBatchResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_import_file(
    business_unit_id: Annotated[uuid.UUID, Form(...)],
    import_type: Annotated[str, Form(...)],
    file: Annotated[UploadFile, File(...)],
    command: Annotated[UploadImportFileCommand, Depends(get_upload_import_file_command)],
) -> ImportBatchResponse:
    """Accept an uploaded file and create import batch metadata."""

    batch = command.execute(
        business_unit_id=business_unit_id,
        import_type=import_type,
        upload=file,
    )
    return ImportBatchResponse.model_validate(batch)


@router.get("/batches", response_model=list[ImportBatchResponse])
def list_import_batches(
    query: Annotated[ListImportBatchesQuery, Depends(get_list_import_batches_query)],
    business_unit_id: uuid.UUID | None = Query(default=None),
) -> list[ImportBatchResponse]:
    """List uploaded import batches and their stored file metadata."""

    batches = query.execute(business_unit_id=business_unit_id)
    return [ImportBatchResponse.model_validate(batch) for batch in batches]


@router.get("/batches/{batch_id}/rows", response_model=list[ImportRowResponse])
def list_import_rows(
    batch_id: uuid.UUID,
    query: Annotated[ListImportRowsQuery, Depends(get_list_import_rows_query)],
    limit: int = Query(default=20, ge=1, le=100),
) -> list[ImportRowResponse]:
    """Return the first staged rows for one batch."""

    try:
        items = query.execute(batch_id=batch_id, limit=limit)
    except ImportBatchRowsNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return [ImportRowResponse.model_validate(item) for item in items]


@router.get("/batches/{batch_id}/errors", response_model=list[ImportRowErrorResponse])
def list_import_errors(
    batch_id: uuid.UUID,
    query: Annotated[ListImportErrorsQuery, Depends(get_list_import_errors_query)],
    limit: int = Query(default=20, ge=1, le=100),
) -> list[ImportRowErrorResponse]:
    """Return the first stored parse errors for one batch."""

    try:
        items = query.execute(batch_id=batch_id, limit=limit)
    except ImportBatchErrorsNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return [ImportRowErrorResponse.model_validate(item) for item in items]


@router.post("/batches/{batch_id}/parse", response_model=ImportBatchResponse)
def parse_import_batch(
    batch_id: uuid.UUID,
    command: Annotated[ParseImportBatchCommand, Depends(get_parse_import_batch_command)],
) -> ImportBatchResponse:
    """Parse an uploaded batch into staging rows and parse errors."""

    try:
        batch = command.execute(batch_id=batch_id)
    except ImportBatchNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ImportBatchStateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return ImportBatchResponse.model_validate(batch)
