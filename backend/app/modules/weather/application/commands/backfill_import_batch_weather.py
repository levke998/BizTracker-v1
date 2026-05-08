"""Backfill weather from an import batch recommendation."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.modules.weather.application.commands.backfill_weather import (
    BackfillWeatherCommand,
    WeatherBackfillSummary,
    WeatherValidationError,
)
from app.modules.weather.application.queries.import_batch_weather import (
    GetImportBatchWeatherRecommendationQuery,
    ImportBatchWeatherNotFoundError,
)


@dataclass(slots=True)
class BackfillImportBatchWeatherCommand:
    """Start weather backfill for the date range covered by one parsed import batch."""

    recommendation_query: GetImportBatchWeatherRecommendationQuery
    backfill_command: BackfillWeatherCommand

    def execute(self, *, batch_id: uuid.UUID) -> WeatherBackfillSummary:
        recommendation = self.recommendation_query.execute(batch_id=batch_id)
        if not recommendation.can_backfill:
            raise WeatherValidationError(recommendation.reason or "Weather backfill is not available.")
        if recommendation.start_date is None or recommendation.end_date is None:
            raise WeatherValidationError("The import batch does not have a weather date range.")

        return self.backfill_command.execute(
            business_unit_id=None,
            name=recommendation.suggested_location_name,
            latitude=recommendation.latitude,
            longitude=recommendation.longitude,
            start_date=recommendation.start_date,
            end_date=recommendation.end_date,
            timezone_name=recommendation.timezone_name,
            scope="shared",
            provider_name=recommendation.provider_name,
        )


__all__ = ["BackfillImportBatchWeatherCommand", "ImportBatchWeatherNotFoundError"]
