"""Minimal CSV parser for staging-level import processing."""

from __future__ import annotations

import csv
import re
import uuid
from pathlib import Path
from typing import Any

from app.modules.imports.application.services.import_profiles import (
    get_import_profile,
)
from app.modules.imports.application.services.gourmand_pos_sales_parser import (
    GourmandPosSalesParser,
)
from app.modules.imports.domain.entities.import_batch import (
    ImportFile,
    NewImportRow,
    NewImportRowError,
    ParsedImportFileResult,
)


class CsvImportParser:
    """Parse one stored CSV file into staging rows and parse errors."""

    paired_pos_import_types = {"gourmand_pos_sales", "flow_pos_sales"}

    def parse_batch(
        self,
        *,
        files: tuple[ImportFile, ...],
        import_type: str,
    ) -> ParsedImportFileResult | None:
        if import_type not in self.paired_pos_import_types:
            return None

        return GourmandPosSalesParser(import_profile=import_type).parse_files(files=files)

    def parse(
        self,
        *,
        file_id: uuid.UUID,
        file_path: str,
        import_type: str,
    ) -> ParsedImportFileResult:
        path = Path(file_path)
        try:
            with path.open("r", encoding="utf-8", newline="") as file_object:
                header_reader = csv.reader(file_object)
                raw_headers = next(header_reader, None)
                if raw_headers is None:
                    return self._file_error_result(
                        file_id=file_id,
                        error_code="missing_header",
                        message="The CSV file does not contain a usable header row.",
                    )

                normalized_headers = [self._normalize_header(header) for header in raw_headers]
                if not any(normalized_headers) or any(not header for header in normalized_headers):
                    return self._file_error_result(
                        file_id=file_id,
                        error_code="missing_header",
                        message="The CSV header contains empty or unusable column names.",
                    )

                if len(set(normalized_headers)) != len(normalized_headers):
                    return self._file_error_result(
                        file_id=file_id,
                        error_code="duplicate_header",
                        message="The CSV header contains duplicate columns after normalization.",
                        raw_payload={
                            "headers": raw_headers,
                            "normalized_headers": normalized_headers,
                        },
                    )

                profile = get_import_profile(import_type)
                if profile is not None:
                    validation_error = profile.validate_headers(
                        normalized_headers=normalized_headers
                    )
                    if validation_error is not None:
                        return self._file_error_result(
                            file_id=file_id,
                            error_code=validation_error.error_code,
                            message=validation_error.message,
                            raw_payload=validation_error.raw_payload,
                        )

                dict_reader = csv.DictReader(file_object, fieldnames=normalized_headers)
                rows: list[NewImportRow] = []
                errors: list[NewImportRowError] = []
                total_rows = 0
                parsed_rows = 0
                error_rows = 0

                row_number = 2
                while True:
                    try:
                        raw_row = next(dict_reader)
                    except StopIteration:
                        break
                    except (UnicodeDecodeError, csv.Error) as exc:
                        errors.append(
                            NewImportRowError(
                                file_id=file_id,
                                row_number=None,
                                field_name=None,
                                error_code="file_read_error",
                                message=str(exc),
                                raw_payload=None,
                            )
                        )
                        error_rows += 1
                        break

                    total_rows += 1
                    current_row_number = row_number
                    row_number += 1
                    try:
                        raw_payload = self._build_raw_payload(raw_row)
                        if self._is_empty_row(raw_payload):
                            rows.append(
                                NewImportRow(
                                    file_id=file_id,
                                    row_number=current_row_number,
                                    raw_payload=raw_payload,
                                    normalized_payload=None,
                                    parse_status="skipped",
                                )
                            )
                            continue

                        normalized_payload = self._normalize_row_payload(
                            raw_payload=raw_payload,
                            profile=profile,
                        )
                        rows.append(
                            NewImportRow(
                                file_id=file_id,
                                row_number=current_row_number,
                                raw_payload=raw_payload,
                                normalized_payload=normalized_payload,
                                parse_status="parsed",
                            )
                        )
                        parsed_rows += 1
                    except Exception as exc:
                        error_rows += 1
                        rows.append(
                            NewImportRow(
                                file_id=file_id,
                                row_number=current_row_number,
                                raw_payload=self._safe_raw_payload(raw_row),
                                normalized_payload=None,
                                parse_status="error",
                            )
                        )
                        errors.append(
                            NewImportRowError(
                                file_id=file_id,
                                row_number=current_row_number,
                                field_name=None,
                                error_code="row_processing_error",
                                message=str(exc),
                                raw_payload=self._safe_raw_payload(raw_row),
                            )
                        )

                return ParsedImportFileResult(
                    rows=rows,
                    errors=errors,
                    total_rows=total_rows,
                    parsed_rows=parsed_rows,
                    error_rows=error_rows,
                )
        except (OSError, UnicodeDecodeError, csv.Error) as exc:
            return self._file_error_result(
                file_id=file_id,
                error_code="file_read_error",
                message=str(exc),
            )

    @staticmethod
    def _normalize_header(value: str | None) -> str:
        header = (value or "").strip().lower()
        header = re.sub(r"\s+", "_", header)
        return header

    @staticmethod
    def _normalize_value(value: Any) -> Any:
        if isinstance(value, str):
            return value.strip()
        return value

    def _normalize_row_payload(
        self,
        *,
        raw_payload: dict[str, Any],
        profile: Any,
    ) -> dict[str, Any]:
        if profile is not None and hasattr(profile, "normalize_row"):
            return profile.normalize_row(raw_payload=raw_payload)

        return {
            key: self._normalize_value(value)
            for key, value in raw_payload.items()
        }

    @staticmethod
    def _is_empty_row(raw_payload: dict[str, Any]) -> bool:
        return all(
            value is None or (isinstance(value, str) and value.strip() == "")
            for value in raw_payload.values()
        )

    def _build_raw_payload(self, raw_row: dict[str | None, Any]) -> dict[str, Any]:
        payload = self._safe_raw_payload(raw_row)
        if "__extra__" in payload:
            raise ValueError("The row contains more columns than the CSV header.")
        return payload

    @staticmethod
    def _safe_raw_payload(raw_row: dict[str | None, Any]) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        for key, value in raw_row.items():
            if key is None:
                payload["__extra__"] = value
            else:
                payload[key] = value
        return payload

    @staticmethod
    def _file_error_result(
        *,
        file_id: uuid.UUID,
        error_code: str,
        message: str,
        raw_payload: dict[str, Any] | None = None,
    ) -> ParsedImportFileResult:
        return ParsedImportFileResult(
            rows=[],
            errors=[
                NewImportRowError(
                    file_id=file_id,
                    row_number=None,
                    field_name=None,
                    error_code=error_code,
                    message=message,
                    raw_payload=raw_payload,
                )
            ],
            total_rows=0,
            parsed_rows=0,
            error_rows=1,
        )
