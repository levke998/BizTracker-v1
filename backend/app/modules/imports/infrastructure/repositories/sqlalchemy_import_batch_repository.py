"""SQLAlchemy import batch repository."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Select, select
from sqlalchemy.orm import Session, selectinload

from app.modules.imports.domain.entities.import_batch import (
    ImportBatch,
    ImportFile,
    ImportRow,
    ImportRowError,
    NewImportRow,
    NewImportRowError,
)
from app.modules.imports.infrastructure.orm.import_batch_model import ImportBatchModel
from app.modules.imports.infrastructure.orm.import_file_model import ImportFileModel
from app.modules.imports.infrastructure.orm.import_row_error_model import (
    ImportRowErrorModel,
)
from app.modules.imports.infrastructure.orm.import_row_model import ImportRowModel


class SqlAlchemyImportBatchRepository:
    """SQLAlchemy-backed repository for import batches."""

    def __init__(self, session: Session) -> None:
        self._session = session

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
        with self._session.begin():
            batch = ImportBatchModel(
                business_unit_id=business_unit_id,
                import_type=import_type,
                status="uploaded",
            )
            self._session.add(batch)
            self._session.flush()

            import_file = ImportFileModel(
                batch_id=batch.id,
                original_name=original_name,
                stored_path=stored_path,
                mime_type=mime_type,
                size_bytes=size_bytes,
            )
            self._session.add(import_file)
            self._session.flush()

            self._session.refresh(batch)

        statement: Select[tuple[ImportBatchModel]] = (
            select(ImportBatchModel)
            .options(selectinload(ImportBatchModel.files))
            .where(ImportBatchModel.id == batch.id)
        )
        stored_batch = self._session.scalars(statement).one()
        return self._to_entity(stored_batch)

    def get_batch(self, batch_id: uuid.UUID) -> ImportBatch | None:
        statement: Select[tuple[ImportBatchModel]] = (
            select(ImportBatchModel)
            .options(
                selectinload(ImportBatchModel.files),
                selectinload(ImportBatchModel.rows),
                selectinload(ImportBatchModel.errors),
            )
            .where(ImportBatchModel.id == batch_id)
        )
        model = self._session.scalars(statement).one_or_none()
        if model is None:
            return None
        return self._to_entity(model)

    def list_rows(
        self,
        *,
        batch_id: uuid.UUID,
        limit: int = 20,
    ) -> list[ImportRow]:
        statement: Select[tuple[ImportRowModel]] = (
            select(ImportRowModel)
            .where(ImportRowModel.batch_id == batch_id)
            .order_by(ImportRowModel.row_number.asc())
            .limit(limit)
        )
        items = self._session.scalars(statement).all()
        return [
            ImportRow(
                id=row.id,
                batch_id=row.batch_id,
                file_id=row.file_id,
                row_number=row.row_number,
                raw_payload=row.raw_payload,
                normalized_payload=row.normalized_payload,
                parse_status=row.parse_status,
                created_at=row.created_at,
            )
            for row in items
        ]

    def list_errors(
        self,
        *,
        batch_id: uuid.UUID,
        limit: int = 20,
    ) -> list[ImportRowError]:
        statement: Select[tuple[ImportRowErrorModel]] = (
            select(ImportRowErrorModel)
            .where(ImportRowErrorModel.batch_id == batch_id)
            .order_by(
                ImportRowErrorModel.row_number.asc().nulls_last(),
                ImportRowErrorModel.created_at.asc(),
            )
            .limit(limit)
        )
        items = self._session.scalars(statement).all()
        return [
            ImportRowError(
                id=error.id,
                batch_id=error.batch_id,
                file_id=error.file_id,
                row_number=error.row_number,
                field_name=error.field_name,
                error_code=error.error_code,
                message=error.message,
                raw_payload=error.raw_payload,
                created_at=error.created_at,
            )
            for error in items
        ]

    def mark_parsing(self, batch_id: uuid.UUID) -> ImportBatch:
        with self._session.begin():
            batch = self._session.get(ImportBatchModel, batch_id)
            if batch is None:
                raise ValueError(f"Import batch {batch_id} was not found.")

            batch.status = "parsing"
            batch.started_at = datetime.now(timezone.utc)
            batch.finished_at = None
            batch.total_rows = 0
            batch.parsed_rows = 0
            batch.error_rows = 0

        return self.get_batch(batch_id)  # type: ignore[return-value]

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
        with self._session.begin():
            batch = self._session.get(ImportBatchModel, batch_id)
            if batch is None:
                raise ValueError(f"Import batch {batch_id} was not found.")

            self._session.add_all(
                [
                    ImportRowModel(
                        batch_id=batch_id,
                        file_id=row.file_id,
                        row_number=row.row_number,
                        raw_payload=dict(row.raw_payload),
                        normalized_payload=(
                            dict(row.normalized_payload)
                            if row.normalized_payload is not None
                            else None
                        ),
                        parse_status=row.parse_status,
                    )
                    for row in rows
                ]
            )
            self._session.add_all(
                [
                    ImportRowErrorModel(
                        batch_id=batch_id,
                        file_id=error.file_id,
                        row_number=error.row_number,
                        field_name=error.field_name,
                        error_code=error.error_code,
                        message=error.message,
                        raw_payload=(
                            dict(error.raw_payload)
                            if error.raw_payload is not None
                            else None
                        ),
                    )
                    for error in errors
                ]
            )

            batch.status = "parsed"
            batch.finished_at = datetime.now(timezone.utc)
            batch.total_rows = total_rows
            batch.parsed_rows = parsed_rows
            batch.error_rows = error_rows

        return self.get_batch(batch_id)  # type: ignore[return-value]

    def mark_failed(
        self,
        *,
        batch_id: uuid.UUID,
        errors: list[NewImportRowError],
        total_rows: int,
        parsed_rows: int,
        error_rows: int,
    ) -> ImportBatch:
        with self._session.begin():
            batch = self._session.get(ImportBatchModel, batch_id)
            if batch is None:
                raise ValueError(f"Import batch {batch_id} was not found.")

            self._session.add_all(
                [
                    ImportRowErrorModel(
                        batch_id=batch_id,
                        file_id=error.file_id,
                        row_number=error.row_number,
                        field_name=error.field_name,
                        error_code=error.error_code,
                        message=error.message,
                        raw_payload=(
                            dict(error.raw_payload)
                            if error.raw_payload is not None
                            else None
                        ),
                    )
                    for error in errors
                ]
            )

            batch.status = "failed"
            batch.finished_at = datetime.now(timezone.utc)
            batch.total_rows = total_rows
            batch.parsed_rows = parsed_rows
            batch.error_rows = error_rows

        return self.get_batch(batch_id)  # type: ignore[return-value]

    def list_batches(
        self,
        *,
        business_unit_id: uuid.UUID | None = None,
    ) -> list[ImportBatch]:
        statement: Select[tuple[ImportBatchModel]] = (
            select(ImportBatchModel)
            .options(selectinload(ImportBatchModel.files))
            .order_by(ImportBatchModel.created_at.desc())
        )
        if business_unit_id is not None:
            statement = statement.where(
                ImportBatchModel.business_unit_id == business_unit_id
            )

        items = self._session.scalars(statement).all()
        return [self._to_entity(item) for item in items]

    @staticmethod
    def _to_entity(model: ImportBatchModel) -> ImportBatch:
        return ImportBatch(
            id=model.id,
            business_unit_id=model.business_unit_id,
            import_type=model.import_type,
            status=model.status,
            started_at=model.started_at,
            finished_at=model.finished_at,
            total_rows=model.total_rows,
            parsed_rows=model.parsed_rows,
            error_rows=model.error_rows,
            created_at=model.created_at,
            updated_at=model.updated_at,
            files=tuple(
                ImportFile(
                    id=file.id,
                    batch_id=file.batch_id,
                    original_name=file.original_name,
                    stored_path=file.stored_path,
                    mime_type=file.mime_type,
                    size_bytes=file.size_bytes,
                    uploaded_at=file.uploaded_at,
                )
                for file in model.files
            ),
            rows=tuple(
                ImportRow(
                    id=row.id,
                    batch_id=row.batch_id,
                    file_id=row.file_id,
                    row_number=row.row_number,
                    raw_payload=row.raw_payload,
                    normalized_payload=row.normalized_payload,
                    parse_status=row.parse_status,
                    created_at=row.created_at,
                )
                for row in getattr(model, "rows", [])
            ),
            errors=tuple(
                ImportRowError(
                    id=error.id,
                    batch_id=error.batch_id,
                    file_id=error.file_id,
                    row_number=error.row_number,
                    field_name=error.field_name,
                    error_code=error.error_code,
                    message=error.message,
                    raw_payload=error.raw_payload,
                    created_at=error.created_at,
                )
                for error in getattr(model, "errors", [])
            ),
        )
