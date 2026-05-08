"""Gourmand POS CSV parser for paired summary/detail exports."""

from __future__ import annotations

import csv
import re
import uuid
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from app.modules.imports.domain.entities.import_batch import (
    ImportFile,
    NewImportRow,
    NewImportRowError,
    ParsedImportFileResult,
)

APP_TIME_ZONE = ZoneInfo("Europe/Budapest")


@dataclass(frozen=True, slots=True)
class _GourmandFileRows:
    file: ImportFile
    rows: list[list[str]]
    source_type: str
    period_start: date | None
    period_end: date | None


class GourmandPosSalesParser:
    """Parse Gourmand's real POS exports into normalized pos_sales rows."""

    detail_source_type = "gourmand_detail"
    summary_source_type = "gourmand_summary"
    _detail_date_pattern = re.compile(r"^\d{4}\.\d{2}\.\d{2}\. \d{2}:\d{2}$")
    _metadata_period_pattern = re.compile(
        r"Adatok:\s*(\d{4}\.\d{2}\.\d{2}\.)\s*-\s*(\d{4}\.\d{2}\.\d{2}\.)"
    )

    def __init__(self, *, import_profile: str = "gourmand_pos_sales") -> None:
        self.import_profile = import_profile
        self.import_source = f"{import_profile}_csv"

    def parse_files(self, *, files: tuple[ImportFile, ...]) -> ParsedImportFileResult:
        loaded_files = [self._load_file(file) for file in files]
        summary_files = [
            loaded_file
            for loaded_file in loaded_files
            if loaded_file.source_type == self.summary_source_type
        ]
        detail_files = [
            loaded_file
            for loaded_file in loaded_files
            if loaded_file.source_type == self.detail_source_type
        ]
        unknown_files = [
            loaded_file
            for loaded_file in loaded_files
            if loaded_file.source_type not in {self.summary_source_type, self.detail_source_type}
        ]

        errors: list[NewImportRowError] = []
        for loaded_file in unknown_files:
            errors.append(
                NewImportRowError(
                    file_id=loaded_file.file.id,
                    row_number=None,
                    field_name=None,
                    error_code="unsupported_gourmand_csv",
                    message=(
                        "A Gourmand import csak tételes lekérdezés és összesített "
                        "lekérdezés CSV fájlokat tud fogadni."
                    ),
                    raw_payload={"original_name": loaded_file.file.original_name},
                )
            )

        if not summary_files:
            return self._blocking_error(
                file_id=files[0].id,
                error_code="missing_gourmand_summary",
                message=(
                    "A Gourmand importhoz szükséges egy összesített lekérdezés is, "
                    "mert ebből érkezik a termékkategória."
                ),
                existing_errors=errors,
            )

        if not detail_files:
            return self._blocking_error(
                file_id=files[0].id,
                error_code="missing_gourmand_detail",
                message=(
                    "A Gourmand importhoz legalább egy tételes lekérdezés szükséges, "
                    "mert ebből érkeznek az időponttal rendelkező eladási sorok."
                ),
                existing_errors=errors,
            )

        period_error = self._validate_metadata_periods(
            summary_files=summary_files,
            detail_files=detail_files,
        )
        if period_error is not None:
            errors.append(period_error)
            return ParsedImportFileResult(
                rows=[],
                errors=errors,
                total_rows=0,
                parsed_rows=0,
                error_rows=len(errors),
            )

        category_by_product = self._build_category_map(summary_files)
        rows: list[NewImportRow] = []
        duplicate_counters: Counter[str] = Counter()
        total_rows = 0
        parsed_rows = 0

        for detail_file in detail_files:
            for row_number, row in enumerate(detail_file.rows, start=1):
                if not self._is_detail_sales_row(row):
                    continue

                total_rows += 1
                parsed = self._parse_detail_row(
                    file=detail_file.file,
                    row=row,
                    row_number=row_number,
                    category_by_product=category_by_product,
                    duplicate_counters=duplicate_counters,
                )
                rows.append(parsed)
                parsed_rows += 1

        return ParsedImportFileResult(
            rows=rows,
            errors=errors,
            total_rows=total_rows,
            parsed_rows=parsed_rows,
            error_rows=len(errors),
        )

    def _load_file(self, file: ImportFile) -> _GourmandFileRows:
        path = Path(file.stored_path)
        with path.open("r", encoding="utf-8-sig", newline="") as file_object:
            rows = list(csv.reader(file_object, delimiter=";"))

        first_cell = self._first_non_empty_cell(rows)
        source_type = "unknown"
        if _looks_like_summary_title(first_cell):
            source_type = self.summary_source_type
        elif _looks_like_detail_title(first_cell):
            source_type = self.detail_source_type

        period_start, period_end = self._extract_metadata_period(rows)

        return _GourmandFileRows(
            file=file,
            rows=rows,
            source_type=source_type,
            period_start=period_start,
            period_end=period_end,
        )

    @staticmethod
    def _first_non_empty_cell(rows: list[list[str]]) -> str:
        for row in rows:
            for value in row:
                cleaned = _clean_text(value)
                if cleaned:
                    return cleaned
        return ""

    def _build_category_map(self, files: list[_GourmandFileRows]) -> dict[str, str]:
        category_by_product: dict[str, str] = {}
        for loaded_file in files:
            for row in loaded_file.rows:
                if len(row) < 6:
                    continue
                product_name = _clean_text(row[0])
                category_name = _clean_text(row[1])
                paid_flag = _clean_text(row[4])
                if not product_name or product_name == "NÉV":
                    continue
                if product_name.startswith("Összesen"):
                    continue
                if paid_flag != "Igen":
                    continue
                if category_name:
                    category_by_product[product_name] = category_name
        return category_by_product

    def _validate_metadata_periods(
        self,
        *,
        summary_files: list[_GourmandFileRows],
        detail_files: list[_GourmandFileRows],
    ) -> NewImportRowError | None:
        summary_periods = {
            (file.period_start, file.period_end)
            for file in summary_files
            if file.period_start is not None and file.period_end is not None
        }
        detail_periods = [
            (file.period_start, file.period_end)
            for file in detail_files
            if file.period_start is not None and file.period_end is not None
        ]

        if not summary_periods or not detail_periods:
            return None

        if len(summary_periods) > 1:
            return NewImportRowError(
                file_id=summary_files[0].file.id,
                row_number=None,
                field_name=None,
                error_code="pos_period_mismatch",
                message="Az osszesito POS fajlok metadata idoszaka nem egyezik.",
                raw_payload={
                    "summary_periods": [
                        _format_period(start, end) for start, end in sorted(summary_periods)
                    ]
                },
            )

        summary_start, summary_end = next(iter(summary_periods))
        detail_start = min(start for start, _end in detail_periods if start is not None)
        detail_end = max(end for _start, end in detail_periods if end is not None)

        if summary_start == detail_start and summary_end == detail_end:
            return None

        return NewImportRowError(
            file_id=detail_files[0].file.id,
            row_number=None,
            field_name=None,
            error_code="pos_period_mismatch",
            message=(
                "Az osszesito es teteles POS CSV-k metadata idoszaka nem egyezik. "
                "Egy forgalmi csomagban ugyanazt az uzleti idoszakot kell lefedniuk."
            ),
            raw_payload={
                "summary_period": _format_period(summary_start, summary_end),
                "detail_combined_period": _format_period(detail_start, detail_end),
            },
        )

    def _extract_metadata_period(
        self,
        rows: list[list[str]],
    ) -> tuple[date | None, date | None]:
        for row in rows[:8]:
            line = " ".join(_clean_text(value) for value in row if _clean_text(value))
            match = self._metadata_period_pattern.search(line)
            if match is None:
                continue
            return (
                _parse_metadata_date(match.group(1)),
                _parse_metadata_date(match.group(2)),
            )
        return None, None

    def _is_detail_sales_row(self, row: list[str]) -> bool:
        return len(row) >= 6 and bool(self._detail_date_pattern.match(_clean_text(row[0])))

    def _parse_detail_row(
        self,
        *,
        file: ImportFile,
        row: list[str],
        row_number: int,
        category_by_product: dict[str, str],
        duplicate_counters: Counter[str],
    ) -> NewImportRow:
        raw_date = _clean_text(row[0])
        user_name = _clean_text(row[1])
        product_name = _clean_text(row[2])
        unit_price = _parse_money(row[3])
        quantity = _parse_number(row[4])
        gross_amount = _parse_money(row[5])
        occurred_at = datetime.strptime(raw_date, "%Y.%m.%d. %H:%M").replace(
            tzinfo=APP_TIME_ZONE
        )
        discount_note = _extract_discount_note(row[5])
        category_name = category_by_product.get(product_name)

        duplicate_base_key = "|".join(
            [
                occurred_at.isoformat(),
                user_name,
                product_name,
                str(_json_number(quantity)),
                str(_json_number(gross_amount)),
            ]
        )
        duplicate_counters[duplicate_base_key] += 1
        source_line_key = f"{self.import_source}:{duplicate_base_key}:{duplicate_counters[duplicate_base_key]}"
        receipt_no = f"GOURMAND-{occurred_at:%Y%m%d-%H%M}-{user_name or 'unknown'}"

        raw_payload: dict[str, Any] = {
            "source_file_type": self.detail_source_type,
            "source_file_name": file.original_name,
            "source_row_number": row_number,
            "date": raw_date,
            "user": user_name,
            "product_name": product_name,
            "unit_price": _clean_text(row[3]),
            "quantity": _clean_text(row[4]),
            "gross_amount": _clean_text(row[5]),
        }
        if discount_note is not None:
            raw_payload["discount_note"] = discount_note

        normalized_payload: dict[str, Any] = {
            "date": occurred_at.date().isoformat(),
            "occurred_at": occurred_at.isoformat(),
            "receipt_no": receipt_no,
            "product_id": None,
            "sku": None,
            "category_name": category_name,
            "product_name": product_name,
            "quantity": _json_number(quantity),
            "gross_amount": _json_number(gross_amount),
            "unit_price": _json_number(unit_price),
            "payment_method": None,
            "source_import_profile": self.import_profile,
            "source_line_key": source_line_key,
            "quantity_basis": "mixed",
            "cashier_name": user_name or None,
        }
        if discount_note is not None:
            normalized_payload["discount_note"] = discount_note

        return NewImportRow(
            file_id=file.id,
            row_number=row_number,
            raw_payload=raw_payload,
            normalized_payload=normalized_payload,
            parse_status="parsed",
        )

    @staticmethod
    def _blocking_error(
        *,
        file_id: uuid.UUID,
        error_code: str,
        message: str,
        existing_errors: list[NewImportRowError],
    ) -> ParsedImportFileResult:
        return ParsedImportFileResult(
            rows=[],
            errors=[
                *existing_errors,
                NewImportRowError(
                    file_id=file_id,
                    row_number=None,
                    field_name=None,
                    error_code=error_code,
                    message=message,
                    raw_payload=None,
                ),
            ],
            total_rows=0,
            parsed_rows=0,
            error_rows=len(existing_errors) + 1,
        )


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    return _normalize_hungarian_text(str(value).strip().lstrip("\ufeff"))


def _normalize_hungarian_text(value: str) -> str:
    return (
        value.replace("õ", "ő")
        .replace("Õ", "Ő")
        .replace("û", "ű")
        .replace("Û", "Ű")
    )


def _looks_like_summary_title(value: str) -> bool:
    normalized = value.upper()
    return normalized.startswith("NAPI") and "SSZ" in normalized


def _looks_like_detail_title(value: str) -> bool:
    normalized = value.upper()
    return normalized.startswith("T") and "RENDEL" in normalized


def _parse_money(value: Any) -> Decimal:
    text = _clean_text(value)
    before_currency = text.split("Ft")[0]
    compact = before_currency.replace(" ", "").replace("\xa0", "").replace(",", ".")
    compact = re.sub(r"[^0-9.\-]", "", compact)
    if compact in {"", "-", ".", "-."}:
        return Decimal("0")
    try:
        return Decimal(compact)
    except InvalidOperation:
        return Decimal("0")


def _parse_number(value: Any) -> Decimal:
    text = _clean_text(value)
    compact = text.replace(" ", "").replace("\xa0", "").replace(",", ".")
    compact = re.sub(r"[^0-9.\-]", "", compact)
    if compact in {"", "-", ".", "-."}:
        return Decimal("0")
    try:
        return Decimal(compact)
    except InvalidOperation:
        return Decimal("0")


def _json_number(value: Decimal) -> int | float:
    if value == value.to_integral_value():
        return int(value)
    return float(value)


def _extract_discount_note(value: Any) -> str | None:
    text = _clean_text(value)
    if "," not in text:
        return None
    note = text.split(",", 1)[1].strip()
    return note or None


def _parse_metadata_date(value: str) -> date:
    return datetime.strptime(value, "%Y.%m.%d.").date()


def _format_period(start: date | None, end: date | None) -> dict[str, str | None]:
    return {
        "start": start.isoformat() if start is not None else None,
        "end": end.isoformat() if end is not None else None,
    }
