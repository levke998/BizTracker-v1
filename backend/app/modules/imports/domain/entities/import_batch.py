"""Import batch domain entities."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class ImportFile:
    """Represents a stored uploaded file that belongs to an import batch."""

    id: uuid.UUID
    batch_id: uuid.UUID
    original_name: str
    stored_path: str
    mime_type: str | None
    size_bytes: int
    uploaded_at: datetime


@dataclass(frozen=True, slots=True)
class NewImportFile:
    """Draft uploaded file metadata used before persistence."""

    original_name: str
    stored_path: str
    mime_type: str | None
    size_bytes: int


@dataclass(frozen=True, slots=True)
class ImportRow:
    """Represents one staging row produced by the parsing pipeline."""

    id: uuid.UUID
    batch_id: uuid.UUID
    file_id: uuid.UUID
    row_number: int
    raw_payload: Mapping[str, Any]
    normalized_payload: Mapping[str, Any] | None
    parse_status: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class ImportRowError:
    """Represents one stored parse error."""

    id: uuid.UUID
    batch_id: uuid.UUID
    file_id: uuid.UUID
    row_number: int | None
    field_name: str | None
    error_code: str
    message: str
    raw_payload: Mapping[str, Any] | None
    created_at: datetime


@dataclass(frozen=True, slots=True)
class NewImportRow:
    """Draft staging row used before persistence."""

    file_id: uuid.UUID
    row_number: int
    raw_payload: Mapping[str, Any]
    normalized_payload: Mapping[str, Any] | None
    parse_status: str


@dataclass(frozen=True, slots=True)
class NewImportRowError:
    """Draft parse error used before persistence."""

    file_id: uuid.UUID
    row_number: int | None
    field_name: str | None
    error_code: str
    message: str
    raw_payload: Mapping[str, Any] | None


@dataclass(frozen=True, slots=True)
class ImportBatch:
    """Represents an import batch and its uploaded files."""

    id: uuid.UUID
    business_unit_id: uuid.UUID
    import_type: str
    status: str
    started_at: datetime
    finished_at: datetime | None
    total_rows: int
    parsed_rows: int
    error_rows: int
    first_occurred_at: str | None
    last_occurred_at: str | None
    created_at: datetime
    updated_at: datetime
    files: tuple[ImportFile, ...]
    rows: tuple[ImportRow, ...] = ()
    errors: tuple[ImportRowError, ...] = ()


@dataclass(frozen=True, slots=True)
class ParsedImportFileResult:
    """Aggregated parser result for one uploaded file."""

    rows: Sequence[NewImportRow]
    errors: Sequence[NewImportRowError]
    total_rows: int
    parsed_rows: int
    error_rows: int
