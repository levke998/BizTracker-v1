"""Ensure weather cache coverage for parsed POS import batches."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date

from app.modules.weather.application.commands.backfill_import_batch_weather import (
    BackfillImportBatchWeatherCommand,
    ImportBatchWeatherNotFoundError,
)
from app.modules.weather.application.queries.import_batch_weather import (
    GetImportBatchWeatherRecommendationQuery,
)


@dataclass(frozen=True, slots=True)
class ImportBatchWeatherCoverageResult:
    """Business-level result for weather preparation around one import batch."""

    batch_id: uuid.UUID
    status: str
    reason: str | None
    start_date: date | None
    end_date: date | None
    requested_hours: int
    cached_hours: int
    missing_hours: int
    backfill_attempted: bool
    created_count: int
    updated_count: int
    skipped_count: int


@dataclass(slots=True)
class EnsureImportBatchWeatherCoverageCommand:
    """Ensure shared Szolnok weather data exists for an import batch time range."""

    recommendation_query: GetImportBatchWeatherRecommendationQuery
    backfill_command: BackfillImportBatchWeatherCommand

    def execute(self, *, batch_id: uuid.UUID) -> ImportBatchWeatherCoverageResult:
        recommendation = self.recommendation_query.execute(batch_id=batch_id)
        if not recommendation.can_backfill:
            return ImportBatchWeatherCoverageResult(
                batch_id=recommendation.batch_id,
                status="skipped",
                reason=recommendation.reason,
                start_date=recommendation.start_date,
                end_date=recommendation.end_date,
                requested_hours=recommendation.requested_hours,
                cached_hours=recommendation.cached_hours,
                missing_hours=recommendation.missing_hours,
                backfill_attempted=False,
                created_count=0,
                updated_count=0,
                skipped_count=0,
            )

        if recommendation.missing_hours == 0:
            return ImportBatchWeatherCoverageResult(
                batch_id=recommendation.batch_id,
                status="covered",
                reason=None,
                start_date=recommendation.start_date,
                end_date=recommendation.end_date,
                requested_hours=recommendation.requested_hours,
                cached_hours=recommendation.cached_hours,
                missing_hours=0,
                backfill_attempted=False,
                created_count=0,
                updated_count=0,
                skipped_count=recommendation.requested_hours,
            )

        summary = self.backfill_command.execute(batch_id=batch_id)
        return ImportBatchWeatherCoverageResult(
            batch_id=recommendation.batch_id,
            status="backfilled",
            reason=None,
            start_date=summary.start_date,
            end_date=summary.end_date,
            requested_hours=summary.requested_hours,
            cached_hours=recommendation.cached_hours + summary.created_count,
            missing_hours=max(
                recommendation.missing_hours - summary.created_count - summary.updated_count,
                0,
            ),
            backfill_attempted=True,
            created_count=summary.created_count,
            updated_count=summary.updated_count,
            skipped_count=summary.skipped_count,
        )


__all__ = [
    "EnsureImportBatchWeatherCoverageCommand",
    "ImportBatchWeatherCoverageResult",
    "ImportBatchWeatherNotFoundError",
]
