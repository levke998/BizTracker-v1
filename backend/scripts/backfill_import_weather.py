"""Backfill shared Szolnok weather data for parsed POS import batches."""

from __future__ import annotations

import argparse
import uuid

from sqlalchemy import select

from app.db.session import SessionLocal
from app.modules.imports.infrastructure.orm.import_batch_model import ImportBatchModel
from app.modules.weather.application.commands.backfill_import_batch_weather import (
    BackfillImportBatchWeatherCommand,
)
from app.modules.weather.application.commands.backfill_weather import BackfillWeatherCommand
from app.modules.weather.application.queries.import_batch_weather import (
    GetImportBatchWeatherRecommendationQuery,
    SUPPORTED_POS_IMPORT_TYPES,
)
from app.modules.weather.application.services.weather_provider import OpenMeteoWeatherProvider
from app.modules.weather.infrastructure.repositories.sqlalchemy_import_weather_repository import (
    SqlAlchemyImportWeatherRepository,
)
from app.modules.weather.infrastructure.repositories.sqlalchemy_weather_repository import (
    SqlAlchemyWeatherRepository,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--batch-id",
        action="append",
        default=[],
        help="Specific import batch id to backfill. Can be passed more than once.",
    )
    args = parser.parse_args()

    batch_ids = [uuid.UUID(value) for value in args.batch_id]

    with SessionLocal() as session:
        import_weather_repository = SqlAlchemyImportWeatherRepository(session)
        weather_repository = SqlAlchemyWeatherRepository(session)
        provider = OpenMeteoWeatherProvider()
        recommendation_query = GetImportBatchWeatherRecommendationQuery(
            repository=import_weather_repository
        )
        command = BackfillImportBatchWeatherCommand(
            recommendation_query=recommendation_query,
            backfill_command=BackfillWeatherCommand(
                repository=weather_repository,
                provider=provider,
            ),
        )

        statement = (
            select(ImportBatchModel.id)
            .where(ImportBatchModel.status == "parsed")
            .where(ImportBatchModel.import_type.in_(SUPPORTED_POS_IMPORT_TYPES))
            .order_by(ImportBatchModel.created_at.asc())
        )
        if batch_ids:
            statement = statement.where(ImportBatchModel.id.in_(batch_ids))

        parsed_batch_ids = list(session.scalars(statement).all())

        total_created = 0
        total_skipped = 0
        total_requested = 0
        for batch_id in parsed_batch_ids:
            recommendation = recommendation_query.execute(batch_id=batch_id)
            if not recommendation.can_backfill or recommendation.missing_hours == 0:
                print(
                    f"{batch_id}: skipped "
                    f"({recommendation.cached_hours}/{recommendation.requested_hours} hours cached)"
                )
                total_requested += recommendation.requested_hours
                total_skipped += recommendation.cached_hours
                continue

            result = command.execute(batch_id=batch_id)
            total_created += result.created_count
            total_skipped += result.skipped_count
            total_requested += result.requested_hours
            print(
                f"{batch_id}: {result.start_date.isoformat()} - {result.end_date.isoformat()}, "
                f"created={result.created_count}, skipped={result.skipped_count}, "
                f"requested={result.requested_hours}"
            )

    print("Import weather backfill completed")
    print(f"Batches: {len(parsed_batch_ids)}")
    print(f"Requested hours: {total_requested}")
    print(f"Created: {total_created}")
    print(f"Skipped: {total_skipped}")


if __name__ == "__main__":
    main()
