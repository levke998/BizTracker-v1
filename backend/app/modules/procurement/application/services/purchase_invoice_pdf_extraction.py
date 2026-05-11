"""Text-layer extraction helpers for supplier invoice PDF drafts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
import re
from typing import Protocol
import unicodedata


@dataclass(frozen=True, slots=True)
class PurchaseInvoicePdfLineCandidate:
    """One line candidate extracted from invoice text."""

    description: str
    quantity: Decimal | None = None
    uom_code: str | None = None
    line_net_amount: Decimal | None = None
    vat_amount: Decimal | None = None
    line_gross_amount: Decimal | None = None
    vat_rate_percent: Decimal | None = None
    confidence_score: Decimal = Decimal("0.20")
    confidence_reasons: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PurchaseInvoicePdfExtractionResult:
    """Structured extraction result before human review."""

    adapter_name: str
    status: str
    text_excerpt: str
    header: dict[str, str]
    lines: tuple[PurchaseInvoicePdfLineCandidate, ...]
    issues: tuple[str, ...]
    confidence_score: Decimal
    confidence_reasons: tuple[str, ...]

    def to_raw_payload(self) -> dict:
        """Return JSON-ready extraction diagnostics for audit/debugging."""

        return {
            "parser": self.adapter_name,
            "status": self.status,
            "text_excerpt": self.text_excerpt,
            "header_candidates": self.header,
            "line_candidates": [
                {
                    key: str(value) if isinstance(value, Decimal) else value
                    for key, value in asdict(line).items()
                }
                for line in self.lines
            ],
            "issues": list(self.issues),
            "confidence_score": str(self.confidence_score),
            "confidence_reasons": list(self.confidence_reasons),
        }


class PurchaseInvoicePdfTextExtractor:
    """Extract visible-ish text from simple PDF text layers without OCR dependencies."""

    def extract_text(self, content: bytes) -> str:
        """Return a best-effort decoded text layer."""

        text = content.decode("utf-8", errors="ignore")
        if len(text.strip()) < 10:
            text = content.decode("latin-1", errors="ignore")
        return self._clean_pdf_text(text)

    @staticmethod
    def _clean_pdf_text(text: str) -> str:
        cleaned = text.replace("\x00", " ")
        cleaned = re.sub(r"[<>()[\]{}]", " ", cleaned)
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in cleaned.splitlines()]
        return "\n".join(line for line in lines if line).strip()


class PurchaseInvoicePdfCandidateParser:
    """Parse invoice header and line candidates from extracted text."""

    _HEADER_ALIASES = {
        "invoice_number": ("szamlaszam", "invoice number", "invoice no", "sorszam"),
        "invoice_date": ("kelte", "teljesites", "invoice date", "date"),
        "gross_total": ("fizetendo", "brutto osszesen", "gross total", "total"),
    }
    _LINE_PREFIXES = ("tetel", "item", "line")

    def parse(
        self,
        text: str,
        *,
        adapter_name: str,
    ) -> PurchaseInvoicePdfExtractionResult:
        if not text.strip():
            return PurchaseInvoicePdfExtractionResult(
                adapter_name=adapter_name,
                status="no_text",
                text_excerpt="",
                header={},
                lines=(),
                issues=("missing_text_layer",),
                confidence_score=Decimal("0.00"),
                confidence_reasons=("missing_text_layer",),
            )

        header = self._parse_header(text)
        lines = tuple(self._parse_lines(text))
        issues: list[str] = []
        if not header and not lines:
            issues.append("no_invoice_candidates_found")

        status = "parsed_review_required" if header or lines else "no_candidates"
        confidence_score, confidence_reasons = self._calculate_confidence(
            header=header,
            lines=lines,
            issues=tuple(issues),
        )
        return PurchaseInvoicePdfExtractionResult(
            adapter_name=adapter_name,
            status=status,
            text_excerpt=text[:2000],
            header=header,
            lines=lines,
            issues=tuple(issues),
            confidence_score=confidence_score,
            confidence_reasons=confidence_reasons,
        )

    def _parse_header(self, text: str) -> dict[str, str]:
        header: dict[str, str] = {}
        normalized_text = _normalize_text(text)
        for field_name, aliases in self._HEADER_ALIASES.items():
            for alias in aliases:
                value = self._find_header_value(normalized_text, alias)
                if value:
                    header[field_name] = self._normalize_header_value(field_name, value)
                    break
        return header

    @staticmethod
    def _find_header_value(normalized_text: str, alias: str) -> str | None:
        pattern = re.compile(
            rf"\b{re.escape(alias)}\b\s*[:#-]?\s*(?P<value>[a-z0-9./_-]+(?:\s*huf|\s*ft)?)",
            flags=re.IGNORECASE,
        )
        match = pattern.search(normalized_text)
        if not match:
            return None
        return match.group("value").strip()

    @staticmethod
    def _normalize_header_value(field_name: str, value: str) -> str:
        if field_name == "gross_total":
            parsed = _parse_decimal(value)
            return str(parsed) if parsed is not None else value
        if field_name == "invoice_date":
            match = re.search(r"\d{4}[-./]\d{1,2}[-./]\d{1,2}", value)
            return match.group(0).replace(".", "-").replace("/", "-") if match else value
        return value

    def _parse_lines(self, text: str) -> list[PurchaseInvoicePdfLineCandidate]:
        candidates: list[PurchaseInvoicePdfLineCandidate] = []
        for raw_line in re.split(r"[\r\n]+", text):
            normalized_line = _normalize_text(raw_line)
            if not any(normalized_line.startswith(prefix) for prefix in self._LINE_PREFIXES):
                continue
            candidate = self._parse_line(raw_line)
            if candidate is not None:
                candidates.append(candidate)
        return candidates

    def _parse_line(self, raw_line: str) -> PurchaseInvoicePdfLineCandidate | None:
        _, _, payload = raw_line.partition(":")
        if not payload:
            _, _, payload = raw_line.partition("-")
        parts = [part.strip() for part in payload.split(";") if part.strip()]
        if not parts:
            return None

        description = parts[0]
        values = self._parse_key_values(parts[1:])
        candidate = PurchaseInvoicePdfLineCandidate(
            description=description,
            quantity=_parse_decimal(values.get("quantity")),
            uom_code=values.get("uom"),
            line_net_amount=_parse_decimal(values.get("net")),
            vat_amount=_parse_decimal(values.get("vat")),
            line_gross_amount=_parse_decimal(values.get("gross")),
            vat_rate_percent=_parse_decimal(values.get("vat_rate")),
        )
        return self._with_line_confidence(candidate)

    @staticmethod
    def _parse_key_values(parts: list[str]) -> dict[str, str]:
        aliases = {
            "mennyiseg": "quantity",
            "qty": "quantity",
            "quantity": "quantity",
            "uom": "uom",
            "me": "uom",
            "netto": "net",
            "net": "net",
            "afa": "vat",
            "vat": "vat",
            "brutto": "gross",
            "gross": "gross",
            "afa%": "vat_rate",
            "vat%": "vat_rate",
            "vat_rate": "vat_rate",
        }
        values: dict[str, str] = {}
        for part in parts:
            key, separator, value = part.partition("=")
            if not separator:
                key, separator, value = part.partition(":")
            if not separator:
                continue
            normalized_key = _normalize_text(key).replace(" ", "_")
            target_key = aliases.get(normalized_key)
            if target_key:
                values[target_key] = value.strip()
        return values

    @staticmethod
    def _with_line_confidence(
        candidate: PurchaseInvoicePdfLineCandidate,
    ) -> PurchaseInvoicePdfLineCandidate:
        score = Decimal("0.20")
        reasons: list[str] = ["has_description"]
        if candidate.quantity is not None:
            score += Decimal("0.15")
            reasons.append("has_quantity")
        if candidate.uom_code:
            score += Decimal("0.10")
            reasons.append("has_uom")
        if candidate.line_net_amount is not None:
            score += Decimal("0.15")
            reasons.append("has_net")
        if candidate.vat_amount is not None:
            score += Decimal("0.15")
            reasons.append("has_vat")
        if candidate.line_gross_amount is not None:
            score += Decimal("0.15")
            reasons.append("has_gross")
        if candidate.vat_rate_percent is not None:
            score += Decimal("0.10")
            reasons.append("has_vat_rate")

        return PurchaseInvoicePdfLineCandidate(
            description=candidate.description,
            quantity=candidate.quantity,
            uom_code=candidate.uom_code,
            line_net_amount=candidate.line_net_amount,
            vat_amount=candidate.vat_amount,
            line_gross_amount=candidate.line_gross_amount,
            vat_rate_percent=candidate.vat_rate_percent,
            confidence_score=min(score, Decimal("1.00")),
            confidence_reasons=tuple(reasons),
        )

    @staticmethod
    def _calculate_confidence(
        *,
        header: dict[str, str],
        lines: tuple[PurchaseInvoicePdfLineCandidate, ...],
        issues: tuple[str, ...],
    ) -> tuple[Decimal, tuple[str, ...]]:
        if issues:
            return Decimal("0.00"), issues

        score = Decimal("0.10")
        reasons: list[str] = []
        for field_name in ("invoice_number", "invoice_date", "gross_total"):
            if field_name in header:
                score += Decimal("0.15")
                reasons.append(f"has_{field_name}")
        if lines:
            line_average = sum(
                (line.confidence_score for line in lines),
                Decimal("0.00"),
            ) / Decimal(len(lines))
            score += line_average * Decimal("0.45")
            reasons.append("has_line_candidates")

        return min(score, Decimal("1.00")).quantize(Decimal("0.01")), tuple(reasons)


class PurchaseInvoicePdfExtractionAdapter(Protocol):
    """Adapter contract for invoice PDF extraction implementations."""

    adapter_name: str

    def extract(self, content: bytes) -> PurchaseInvoicePdfExtractionResult:
        """Extract invoice candidates from a PDF byte stream."""


class TextLayerRegexPurchaseInvoicePdfExtractionAdapter:
    """No-dependency PDF text-layer adapter for early invoice prefill."""

    adapter_name = "text_layer_regex_v1"

    def __init__(
        self,
        text_extractor: PurchaseInvoicePdfTextExtractor | None = None,
        candidate_parser: PurchaseInvoicePdfCandidateParser | None = None,
    ) -> None:
        self._text_extractor = text_extractor or PurchaseInvoicePdfTextExtractor()
        self._candidate_parser = candidate_parser or PurchaseInvoicePdfCandidateParser()

    def extract(self, content: bytes) -> PurchaseInvoicePdfExtractionResult:
        text = self._text_extractor.extract_text(content)
        return self._candidate_parser.parse(text, adapter_name=self.adapter_name)


class PurchaseInvoicePdfExtractionService:
    """Coordinate configured invoice PDF extraction adapters."""

    def __init__(
        self,
        adapters: tuple[PurchaseInvoicePdfExtractionAdapter, ...] | None = None,
    ) -> None:
        self._adapters = adapters or (TextLayerRegexPurchaseInvoicePdfExtractionAdapter(),)

    def extract(self, content: bytes) -> PurchaseInvoicePdfExtractionResult:
        # One adapter is active today; the boundary lets OCR/vendor adapters join later.
        return self._adapters[0].extract(content)


def _normalize_text(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    without_accents = "".join(char for char in decomposed if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", without_accents.casefold()).strip()


def _parse_decimal(value: str | None) -> Decimal | None:
    if value is None:
        return None
    cleaned = value.strip().replace("\u00a0", " ").replace(" ", "")
    cleaned = re.sub(r"[^0-9,.-]", "", cleaned)
    if not cleaned:
        return None
    if "," in cleaned and "." in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", ".")
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None
